import asyncio
import logging
from agent_framework import (
    AgentRunUpdateEvent,
    ChatAgent,
    GroupChatBuilder,
    WorkflowOutputEvent,
    MCPStdioTool
)
from agent_framework.openai import OpenAIChatClient
import os

logging.basicConfig(level=logging.INFO)

async def main() -> None:    
    mcp_server = MCPStdioTool(
        name="ecommerce_mcp",
        command="python",
        args=["./mcp-server.py"],
    )
    
    # AGENT 1: Product Intelligence
    
    product_intelligence_agent = ChatAgent(
        name="ProductIntelligenceAgent",
        description="Research specialist that enriches product data with web insights and creates content briefs.",
        instructions=f"""You are a product research analyst specializing in market intelligence.

Your responsibilities:
1. Retrieve internal product data using get_product_catalog()
2. Get brand guidelines using get_brand_guidelines with the product category
3. Use web_search to research:
   - Competitor products in the same category
   - Market trends and consumer preferences
   - Common selling points and terminology
   - Price positioning (budget/mid/premium)
4. Create a comprehensive Content Brief with:
   - Product summary (factual, no marketing fluff)
   - Target audience (based on category and price point)
   - Market positioning (premium/value/sustainable/etc)
   - Key differentiators (from specs + web research)
   - SEO focus terms (5-8 keywords)
   - Brand constraints (tone, forbidden claims, disclaimers)
   - Web insights summary (what you learned from research)

CRITICAL RULES:
- You DO NOT write marketing copy - only research and brief creation
- Base your brief on REAL data from product catalog and web search
- Include specific web insights (e.g., "Gaming mice market emphasizes...")
- Structure your output clearly with headers

Your output will be used by the Content Creator Agent to write marketing content.
""",
        chat_client=OpenAIChatClient(model_id="gpt-4o", api_key=os.environ.get("OPENAI_API_KEY")),
        tools=[mcp_server]
    )
    
    # AGENT 2: Content Creator
    
    content_creator_agent = ChatAgent(
        name="ContentCreatorAgent",
        description="Marketing copywriter that transforms content briefs into persuasive e-commerce content.",
        instructions="""You are an expert e-commerce copywriter specializing in conversion-focused content.

Your responsibilities:
1. Receive the Content Brief from ProductIntelligenceAgent
2. Generate marketing content package:
   - Product Title (compelling, under 200 chars)
   - Short Description (50-500 chars, conversational)
   - Long Description (detailed, includes benefits + disclaimers)
   - Feature Bullets (5-7 bullet points highlighting key specs)
   - Meta Title (SEO-optimized, ~60 chars)
   - Meta Description (SEO-optimized, under 160 chars)
   - Promotional Copy (ad/social media, punchy)

3. Use validation tools:
   - validate_seo_keywords to check keyword usage
   - check_platform_constraints for title/meta length

CRITICAL RULES:
- Follow the brand tone EXACTLY from the brief
- NEVER use forbidden claims from the brief
- ALWAYS include required disclaimers in long description
- Use keywords naturally (don't stuff)
- Stay within character limits
- Every claim must be supported by the brief

Format your output clearly:
=== PRODUCT TITLE ===
[title]

=== SHORT DESCRIPTION ===
[description]

=== LONG DESCRIPTION ===
[description]

=== META TITLE ===
[meta title]

=== META DESCRIPTION ===
[meta description]

=== PROMOTIONAL COPY ===
[promo text]
""",
        chat_client=OpenAIChatClient(model_id="gpt-4o", api_key=os.environ.get("OPENAI_API_KEY")),
        tools=[mcp_server]
    )
    
    # AGENT 3: Quality Control
    
    quality_control_agent = ChatAgent(
        name="QualityControlAgent",
        description="Quality assurance specialist that validates content before publishing.",
        instructions="""You are the final quality gatekeeper for e-commerce content.

Your responsibilities:
1. Receive both the Content Brief AND the Marketing Content
2. Run comprehensive validation checks:
   
   CHECK 1: Fact Consistency
   - Use verify_fact_consistency() to ensure content matches brief
   - Verify all differentiators mentioned
   - Check that no unsupported claims were added
   
   CHECK 2: Brand Compliance  
   - Use check_brand_compliance() to scan for forbidden terms
   - Verify brand tone alignment
   - Confirm required disclaimers are present
   
   CHECK 3: SEO Quality
   - Use validate_seo_keywords() with the brief's focus terms
   - Check for keyword stuffing or underuse
   
   CHECK 4: Readability
   - Use analyze_readability() on the long description
   - Ensure clarity and appropriate reading level
   
   CHECK 5: Platform Rules
   - Use check_platform_constraints() for all content pieces
   - Verify length limits

3. Make final decision:
   - APPROVED (if all checks pass, provide quality score 85-95)
   - NEEDS REVISION (if minor issues, list specific fixes needed)
   - REJECTED (if critical violations like forbidden claims, list all issues)

CRITICAL RULES:
- You CANNOT modify the content, only approve/reject/request revision
- Provide SPECIFIC, ACTIONABLE feedback
- Use deterministic pass/fail logic (no "vibes")
- If rejected, explain exactly what needs to change

Format your output:
=== QUALITY VALIDATION REPORT ===

- FACT CONSISTENCY: [result]
- BRAND COMPLIANCE: [result]  
- SEO QUALITY: [result]
- READABILITY: [result]
- PLATFORM RULES: [result]

DECISION: [APPROVED/NEEDS REVISION/REJECTED]
QUALITY SCORE: [0-100 if approved]

FEEDBACK:
[detailed feedback if not approved]
""",
        chat_client=OpenAIChatClient(model_id="gpt-4o", api_key=os.environ.get("OPENAI_API_KEY")),
        tools=[mcp_server]
    )

    coordinator_agent = ChatAgent(
        name="CoordinatorAgent",
        description="Coordinator that manages a content creation workflow.",
        instructions="""You are coordinating a content creation pipeline with strict ordering.

WORKFLOW SEQUENCE (MUST FOLLOW EXACTLY):
1. ProductIntelligenceAgent - Creates content brief from product data + web research
2. ContentCreatorAgent - Writes marketing content based on the brief
3. QualityControlAgent - Validates content and approves/rejects

COORDINATION RULES:
- ProductIntelligenceAgent ALWAYS goes first
- ContentCreatorAgent can ONLY start after receiving the complete brief
- QualityControlAgent can ONLY start after receiving both brief AND content
- Each agent must fully complete their work before the next begins
- If QualityControlAgent rejects, you may allow ContentCreatorAgent to revise ONCE

COMPLETION CRITERIA:
- Task is complete when QualityControlAgent provides final decision (APPROVED/REJECTED/NEEDS REVISION)
- Do NOT continue after quality report is delivered

Select participants in strict order. Build on previous outputs.
""",
        chat_client=OpenAIChatClient(model_id="gpt-4o", api_key=os.environ.get("OPENAI_API_KEY")),
    )

    workflow = (
        GroupChatBuilder()
        .set_manager(coordinator_agent, display_name="Coordinator")
        .participants([product_intelligence_agent, content_creator_agent, quality_control_agent])
        .build()
    )
    
    task = "Create marketing content for product PROD001"
    
    print(f"TASK: {task}\n")
    print("=" * 80)
    print("WORKFLOW EXECUTION\n\n")
    
    final_response = None
    last_executor_id: str | None = None
    
    async for event in workflow.run_stream(task):
        if isinstance(event, AgentRunUpdateEvent):
            eid = event.executor_id
            if eid != last_executor_id:
                if last_executor_id is not None:
                    print("\n")
                print(f"\n{'='*80}")
                print(f"🤖 {eid}")
                print(f"{'='*80}")
                last_executor_id = eid
            print(event.data, end="", flush=True)
            
        elif isinstance(event, WorkflowOutputEvent):
            final_response = getattr(event.data, "text", str(event.data))
    
    if final_response:
        print("\n\n")
        print("=" * 80)
        print("WORKFLOW COMPLETED")
        print("=" * 80)
        print(final_response)
        print("=" * 80)


if __name__ == "__main__":
    print("""
    Multi-Agent E-commerce Content Creation & Quality System

    Agents:
    1. Product Intelligence Agent (research + web search)
    2. Content Creator Agent (marketing copywriting)
    3. Quality Control Agent (validation + approval)
    """)
    
    asyncio.run(main())