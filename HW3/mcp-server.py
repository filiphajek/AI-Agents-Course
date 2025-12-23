from typing import List
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("ecommerce-content-tools")

# PRODUCT DATA TOOLS

@mcp.tool()
def get_product_catalog(product_id: str) -> str:
    """Retrieve product data from internal catalog.
    
    Args:
        product_id: The product ID (e.g., PROD001, PROD002).
    """
    catalog = {
        "PROD001": {
            "name": "UltraGrip Pro Wireless Mouse",
            "category": "Computer Accessories",
            "price": 49.99,
            "specifications": {
                "DPI": "16000",
                "Buttons": "8 programmable",
                "Battery": "70 hours",
                "Connectivity": "2.4GHz + Bluetooth",
                "Weight": "95g"
            },
            "supplier_notes": "Premium gaming mouse with ergonomic design"
        },
        "PROD002": {
            "name": "EcoBlend Bamboo Coffee Mug",
            "category": "Kitchen & Dining",
            "price": 24.99,
            "specifications": {
                "Material": "Bamboo fiber composite",
                "Capacity": "350ml",
                "Insulation": "Double-walled",
                "Microwave Safe": "No",
                "Dishwasher Safe": "Yes"
            },
            "supplier_notes": "Sustainable, BPA-free travel mug"
        }
    }
    
    if product_id in catalog:
        product = catalog[product_id]
        return f"""
Product: {product['name']}
Category: {product['category']}
Price: ${product['price']}
Specifications: {', '.join([f'{k}: {v}' for k, v in product['specifications'].items()])}
Notes: {product['supplier_notes']}
"""
    return f"Error: Product {product_id} not found"


@mcp.tool()
def get_brand_guidelines(category: str) -> str:
    """Get brand guidelines for product category.
    
    Args:
        category: The product category (e.g., 'Computer Accessories', 'Kitchen & Dining').
    """
    guidelines = {
        "Computer Accessories": """
Brand Tone: Professional, tech-savvy, performance-focused
Forbidden Claims: unbreakable, fastest in the world, medical grade
Required Disclaimers: Performance may vary by system
Compliance: No health claims, Must specify wireless frequency
""",
        "Kitchen & Dining": """
Brand Tone: Warm, eco-conscious, lifestyle-oriented
Forbidden Claims: 100% eco-friendly, zero waste, miracle product
Required Disclaimers: Hand wash recommended for longevity
Compliance: Must mention care instructions, Material sourcing transparency
"""
    }
    return guidelines.get(category, "Brand Tone: Friendly and informative")


# VALIDATION TOOLS

@mcp.tool()
def validate_seo_keywords(content: str, keywords: List[str]) -> str:
    """Analyze keyword placement in content.
    
    Args:
        content: The content text to analyze.
        keywords: List of keywords to check for.
    """
    results = []
    content_lower = content.lower()
    
    for keyword in keywords:
        count = content_lower.count(keyword.lower())
        status = "Good" if 1 <= count <= 5 else "Needs adjustment"
        results.append(f"{keyword}: {count} occurrences - {status}")
    
    return "\n".join(results)


@mcp.tool()
def check_platform_constraints(content_type: str, content: str) -> str:
    """Validate content against platform rules.
    
    Args:
        content_type: Type of content (e.g., 'product_title', 'short_description', 'meta_description').
        content: The content text to validate.
    """
    rules = {
        "product_title": {"max": 200, "min": 10},
        "short_description": {"max": 500, "min": 50},
        "meta_description": {"max": 160, "min": 50}
    }
    
    rule = rules.get(content_type, {"max": 1000, "min": 10})
    length = len(content)
    
    if rule["min"] <= length <= rule["max"]:
        return f"Valid length ({length} chars, limit: {rule['max']})"
    return f"Invalid length ({length} chars, allowed: {rule['min']}-{rule['max']})"


@mcp.tool()
def check_brand_compliance(content: str, forbidden_terms: List[str]) -> str:
    """Check content for forbidden claims.
    
    Args:
        content: The content text to check.
        forbidden_terms: List of forbidden terms/claims to detect.
    """
    content_lower = content.lower()
    violations = []
    
    for term in forbidden_terms:
        if term.lower() in content_lower:
            violations.append(f"Forbidden term detected: '{term}'")
    
    if violations:
        return "\n".join(violations)
    return "No brand violations detected"


@mcp.tool()
def analyze_readability(content: str) -> str:
    """Analyze content readability metrics.
    
    Args:
        content: The content text to analyze.
    """
    word_count = len(content.split())
    avg_word_length = sum(len(word) for word in content.split()) / max(word_count, 1)
    
    level = "8th grade" if avg_word_length < 6 else "College"
    clarity = "Good" if avg_word_length < 6 else "Could be simpler"
    
    return f"""
Word Count: {word_count}
Reading Level: {level}
Clarity: {clarity}
"""


@mcp.tool()
def verify_fact_consistency(brief: str, content: str) -> str:
    """Verify claims in content match the brief.
    
    Args:
        brief: The original content brief.
        content: The marketing content to verify.
    """
    brief_lower = brief.lower()
    content_lower = content.lower()
    
    key_terms = ["dpi", "battery", "bamboo", "capacity", "wireless", "sustainable"]
    missing = []
    
    for term in key_terms:
        if term in brief_lower and term not in content_lower:
            missing.append(f"Brief mentions '{term}' but content doesn't")
    
    if missing:
        return "\n".join(missing)
    return "Content consistent with brief"


if __name__ == "__main__":
    mcp.run(transport='stdio')