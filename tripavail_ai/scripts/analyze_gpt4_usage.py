#!/usr/bin/env python3
"""Analyze GPT-4 usage and cost impact analysis"""

# GPT-4 Usage Locations:
# 1. core/news/editor.py - News analysis & scoring (CRITICAL)
# 2. core/content/story_analyzer.py - Story analysis (CRITICAL) - Currently uses GPT-4o
# 3. core/media/images/generator/gemini_thumbnail_generator.py - Hook text (IMPORTANT)
# 4. core/media/images/generator/hybrid_generator.py - Query optimization (IMPORTANT)
# 5. core/content/intelligence/trending_detector.py - Trending detection (OPTIONAL)

# OpenAI Pricing (as of 2024):
# GPT-4: ~$0.03 per 1K input tokens, ~$0.06 per 1K output tokens
# GPT-4o: ~$0.005 per 1K input tokens, ~$0.015 per 1K output tokens (10x cheaper!)
# GPT-3.5-turbo: ~$0.0005 per 1K input tokens, ~$0.0015 per 1K output tokens (60x cheaper!)
# GPT-4o-mini: ~$0.00015 per 1K input tokens, ~$0.0006 per 1K output tokens (200x cheaper!)

print("="*70)
print("GPT-4 DOWNGRADE IMPACT ANALYSIS")
print("="*70)

usage_analysis = {
    "CRITICAL - News Analysis (core/news/editor.py)": {
        "model": "gpt-4o",
        "frequency": "Every 4 hours (6x/day)",
        "avg_tokens": "~1500 input, ~800 output",
        "current_cost_per_call": "$0.009",
        "current_daily_cost": "$0.05",
        "monthly_cost": "$1.50",
        "gpt-3.5-turbo_cost": "$0.002",
        "gpt-4o-mini_cost": "$0.0005",
        "impact_if_downgraded": "MODERATE - May miss some tourism-relevant articles, lower scoring accuracy",
        "recommendation": "Keep GPT-4o (excellent balance of quality vs. cost)"
    },
    "CRITICAL - Story Analysis (core/content/story_analyzer.py)": {
        "model": "gpt-4o",
        "frequency": "Per post (~6 posts/day = 6x/day)",
        "avg_tokens": "~800 input, ~500 output",
        "current_cost_per_call": "$0.018",  # GPT-4o pricing
        "current_daily_cost": "$0.11",
        "monthly_cost": "$3.24",
        "gpt-3.5-turbo_cost": "$0.001",
        "impact_if_downgraded": "HIGH - Story quality, video parameters, narrative scripts may degrade",
        "recommendation": "Keep GPT-4o or downgrade to GPT-3.5-turbo if cost critical"
    },
    "IMPORTANT - Hook Text (gemini_thumbnail_generator.py)": {
        "model": "gpt-3.5-turbo",
        "frequency": "Per post (~6 posts/day)",
        "avg_tokens": "~150 input, ~20 output",
        "current_cost_per_call": "$0.0001",
        "current_daily_cost": "$0.001",
        "monthly_cost": "$0.03",
        "gpt-3.5-turbo_cost": "$0.0001",
        "impact_if_downgraded": "LOW - Hook text quality may decrease slightly",
        "recommendation": "Already on GPT-3.5-turbo (super cost efficient)"
    },
    "IMPORTANT - Query Optimization (hybrid_generator.py)": {
        "model": "gpt-4o-mini",
        "frequency": "Per query (~10-15 queries/post, ~60-90/day)",
        "avg_tokens": "~100 input, ~20 output",
        "current_cost_per_call": "$0.0002",
        "current_daily_cost": "$0.02",  # 90 queries * $0.0002
        "monthly_cost": "$0.60",
        "gpt-3.5-turbo_cost": "$0.00008",
        "impact_if_downgraded": "LOW-MODERATE - Search query quality may decrease",
        "recommendation": "Currently using GPT-4o-mini (good mix of quality + savings)"
    },
    "OPTIONAL - Trending Detection (trending_detector.py)": {
        "model": "gpt-4",
        "frequency": "Rarely used (optional feature)",
        "avg_tokens": "~2000 input, ~500 output",
        "current_cost_per_call": "$0.12",
        "current_daily_cost": "$0.00",  # Rarely used
        "monthly_cost": "$0.00",
        "recommendation": "Downgrade to GPT-3.5-turbo"
    }
}

print("\n📊 CURRENT COSTS:")
print("-"*70)
total_daily = 0
total_monthly = 0

for task, details in usage_analysis.items():
    print(f"\n{task}:")
    print(f"  Model: {details.get('model', 'N/A')}")
    print(f"  Cost per call: {details.get('current_cost_per_call', 'N/A')}")
    print(f"  Daily cost: {details.get('current_daily_cost', 'N/A')}")
    monthly = details.get('monthly_cost', '$0')
    if monthly != '$0.00':
        total_monthly += float(monthly.replace('$', ''))
    daily = details.get('current_daily_cost', '$0')
    if daily != '$0.00':
        total_daily += float(daily.replace('$', ''))

print(f"\n💵 TOTAL DAILY COST: ${total_daily:.2f}")
print(f"💵 TOTAL MONTHLY COST: ${total_monthly:.2f}")

print("\n\n💰 DOWNGRADE OPTIONS:")
print("-"*70)

print("\n**OPTION 1: Maintain current mix (recommended)**")
print("  - News Analysis on GPT-4o (quality + efficient)")
print("  - Hook Text on GPT-3.5-turbo (ultra low cost)")
print("  - Query Optimization on GPT-4o-mini (balanced results)")
print("  - TOTAL DAILY COST: ≈$0.09/day ($2.70/month)")

print("\n**OPTION 2: Aggressive savings (news → GPT-4o-mini)**")
print("  - News Analysis: $0.05/day → ~$0.02/day")
print("  - Hook Text: stays ~$0.001/day")
print("  - Query Optimization: stays ~$0.02/day")
print("  - NEW TOTAL DAILY COST: ≈$0.04/day ($1.20/month)")
print("  - IMPACT: Slightly lower scoring fidelity; monitor quality closely")

print("\n**OPTION 3: Ultra budget (everything → GPT-3.5-turbo)**")
print("  - News Analysis: $0.05/day → ~$0.009/day")
print("  - Hook Text: unchanged (~$0.001/day)")
print("  - Query Optimization: $0.02/day → ~$0.007/day")
print("  - NEW TOTAL DAILY COST: ≈$0.02/day ($0.60/month)")
print("  - IMPACT: Noticeable drop in analysis depth and query quality")

print("\n\n⚠️ RECOMMENDATIONS BY TASK:")
print("-"*70)
for task, details in usage_analysis.items():
    print(f"\n{task}:")
    print(f"  Impact if downgraded: {details.get('impact_if_downgraded', 'N/A')}")
    print(f"  Recommendation: {details.get('recommendation', 'N/A')}")

print("\n\n🎯 RECOMMENDED STRATEGY:")
print("-"*70)
print("1. Keep GPT-4o for Story Analysis (already optimized).")
print("2. Current mix balances cost & quality at ≈$0.09/day.")
print("3. If more savings needed, test news analysis on GPT-4o-mini and review outputs.")
print("4. Reserve GPT-3.5-only mode for emergency budget cuts; expect quality loss.")
print("\n✅ CURRENT SAVINGS: >90% vs. original GPT-4-only pipeline")
print("✅ IMPACT: Minimal with present configuration; escalate only if finances demand.")

print("\n" + "="*70)

