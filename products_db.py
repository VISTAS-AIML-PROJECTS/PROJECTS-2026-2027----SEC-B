# Skincare Products Knowledge Base (Prices in INR ₹)

PRODUCTS_CATALOG = {
    'acne': [
        {
            'id': 'acne-1',
            'name': 'Clarifying Salicylic Acid 2% Cleanser',
            'brand': 'DermoPure Lab',
            'category': 'Cleanser',
            'icon': '🧼',
            'price': '₹499',
            'tag': 'Best for Active Blemishes',
            'activeIngredients': ['2% Salicylic Acid (BHA)', 'Tea Tree Extract', 'Zinc PCA'],
            'whyItHelps': 'Penetrates deep into pores to dissolve excess sebum, unclog dead skin cells, and rapidly soothe active acne breakouts.',
            'howToUse': 'Massage onto damp face for 60 seconds twice daily. Rinse thoroughly with lukewarm water.'
        },
        {
            'id': 'acne-2',
            'name': 'Niacinamide 10% + Zinc 1% Blemish Serum',
            'brand': 'SkinScience Pro',
            'category': 'Treatment Serum',
            'icon': '🧪',
            'price': '₹649',
            'tag': 'Sebum & Redness Control',
            'activeIngredients': ['10% Niacinamide (Vitamin B3)', '1% Zinc PCA', 'Centella Asiatica'],
            'whyItHelps': 'Reduces skin congestion, regulates oil production, and minimizes post-acne redness and inflammation.',
            'howToUse': 'Apply 3-4 drops to cleansed face morning and night before heavier creams.'
        },
        {
            'id': 'acne-3',
            'name': 'Overnight Hydrocolloid Spot Patches',
            'brand': 'ClearPatch Clinical',
            'category': 'Spot Treatment',
            'icon': '✨',
            'price': '₹349',
            'tag': 'Rapid Overnight Fix',
            'activeIngredients': ['Medical-Grade Hydrocolloid', 'Salicylic Acid Micro-darts'],
            'whyItHelps': 'Absorbs impurities directly from pimples while creating a sterile protective barrier to prevent scarring.',
            'howToUse': 'Cleanse and dry skin, place patch directly over spot, leave on for 6-8 hours or overnight.'
        }
    ],
    'dark_circles': [
        {
            'id': 'dc-1',
            'name': 'Caffeine 5% + EGCG Under-Eye Brightening Serum',
            'brand': 'OptiGlow Clinical',
            'category': 'Eye Serum',
            'icon': '👁️',
            'price': '₹799',
            'tag': 'Micro-Circulation Boost',
            'activeIngredients': ['5% High-Solubility Caffeine', 'Green Tea EGCG', 'Hyaluronic Acid'],
            'whyItHelps': 'Visibly reduces dark shadows under the eyes by stimulating lymphatic drainage and reducing fluid retention.',
            'howToUse': 'Gently dab a small drop around contour of eyes morning and evening using your ring finger.'
        },
        {
            'id': 'dc-2',
            'name': 'Peptide & Vitamin C Radiance Eye Cream',
            'brand': 'Lumiere Botanicals',
            'category': 'Eye Cream',
            'icon': '✨',
            'price': '₹999',
            'tag': 'Collagen & Brightness',
            'activeIngredients': ['Stabilized Vitamin C (THD Ascorbate)', 'Quad-Peptide Complex', 'Niacinamide'],
            'whyItHelps': 'Thickens delicate under-eye skin and inhibits melanin overproduction to fade dark pigmentation circles over time.',
            'howToUse': 'Smooth a pea-sized amount along orbital bone after serum.'
        },
        {
            'id': 'dc-3',
            'name': 'Hydrogel Cooling Eye Patches (30 Pairs)',
            'brand': 'CryoPure Therapy',
            'category': 'Eye Mask',
            'icon': '❄️',
            'price': '₹599',
            'tag': 'Instant Cooling & De-puffing',
            'activeIngredients': ['Cooling Mint Complex', 'Marine Collagen', 'Aloe Vera Juice'],
            'whyItHelps': 'Instantly lowers skin temperature under the eyes, shrinking dilated capillaries that cause dark blueish tones.',
            'howToUse': 'Apply under eyes for 15-20 minutes. Pat remaining serum into skin.'
        }
    ],
    'redness': [
        {
            'id': 'red-1',
            'name': 'Centella Asiatica (CICA) Soothing Gel Relief',
            'brand': 'PhytoCalm Skin',
            'category': 'Calming Relief Gel',
            'icon': '🌿',
            'price': '₹699',
            'tag': 'Instant Redness Reduction',
            'activeIngredients': ['92% Fermented Centella Asiatica', 'Madecassoside', 'Allantoin'],
            'whyItHelps': 'Rapidly extinguishes facial flushing, soothe inflamed skin barriers, and reduces capillary reactivity.',
            'howToUse': 'Apply liberally over cheeks, nose, and flush-prone areas whenever skin feels sensitive or hot.'
        },
        {
            'id': 'red-2',
            'name': 'Ceramide Barrier Repair Intensive Cream',
            'brand': 'SkinBarrier Rx',
            'category': 'Moisturizer',
            'icon': '🛡️',
            'price': '₹899',
            'tag': 'Skin Barrier Protection',
            'activeIngredients': ['Ceramides AP/EOP/NP', 'Colloidal Oatmeal', 'Phytosphingosine'],
            'whyItHelps': 'Rebuilds compromised stratum corneum to shield underlying nerve endings and blood vessels from irritation.',
            'howToUse': 'Use as final step in routine morning and night.'
        }
    ],
    'dryness_texture': [
        {
            'id': 'dry-1',
            'name': 'Triple Hyaluronic Hydration Complex Serum',
            'brand': 'AquaInfuse',
            'category': 'Hydration Serum',
            'icon': '💧',
            'price': '₹749',
            'tag': 'Multi-Depth Moisture',
            'activeIngredients': ['High & Low Molecular Hyaluronic Acid', 'Polyglutamic Acid', 'Pro-Vitamin B5'],
            'whyItHelps': 'Locks moisture across all 3 skin layers, plumping fine dry lines and smoothing rough patches.',
            'howToUse': 'Apply to damp skin immediately after cleansing.'
        },
        {
            'id': 'dry-2',
            'name': 'Gentle Lactic Acid 5% Micro-Exfoliating Solution',
            'brand': 'GlowSmooth Therapy',
            'category': 'Exfoliant',
            'icon': '✨',
            'price': '₹699',
            'tag': 'Surface Texture Refiner',
            'activeIngredients': ['5% Lactic Acid (AHA)', 'Tasmanian Pepperberry', 'Squalane'],
            'whyItHelps': 'Gently dissolves dead flaky skin surface cells without stripping moisture, restoring a soft glowing texture.',
            'howToUse': 'Use 2-3 nights per week on dry clean skin. Follow with moisturizer.'
        }
    ]
}


def get_recommended_products(detected_issues):
    """
    Returns tailored recommendations matching detected issues sorted by severity
    """
    recommendations = []
    added_ids = set()

    sorted_issues = sorted(detected_issues, key=lambda x: x['severity'], reverse=True)

    for issue in sorted_issues:
        catalog_key = issue['key']
        items = PRODUCTS_CATALOG.get(catalog_key, [])

        for item in items:
            if item['id'] not in added_ids:
                added_ids.add(item['id'])
                recommendations.append({
                    **item,
                    'matchedIssue': issue['name'],
                    'issueSeverity': issue['severityText']
                })

    # If no specific issues detected or clear skin
    if not recommendations:
        return [
            {
                **PRODUCTS_CATALOG['acne'][1],
                'matchedIssue': 'Daily Maintenance & Prevention',
                'issueSeverity': 'Clear Skin Protection'
            },
            {
                **PRODUCTS_CATALOG['dark_circles'][0],
                'matchedIssue': 'Eye Area Nourishment',
                'issueSeverity': 'Bright Eye Care'
            },
            {
                **PRODUCTS_CATALOG['dryness_texture'][0],
                'matchedIssue': 'Hydration Lock',
                'issueSeverity': 'Skin Barrier Maintenance'
            }
        ]

    return recommendations
