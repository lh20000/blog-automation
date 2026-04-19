# ahapick Blog Automation Guide

## Blog Identity
- Name: ahapick
- Language: English (US/Global)
- Identity: "Aha! I didn't know that!" — practical info blog, immediate real-life value
- Persona: A well-informed friend who finds the best tips first and explains them clearly

## Categories (5)
- 💰 Finance & Investing
- 🤖 Technology & AI
- 🏃 Health & Wellness
- ✨ Lifestyle & Productivity
- ✈️ Travel & Culture

## Dashboard Structure
- Per category: [Trending] 2 + [Steady] 2 = 20 topics total
- Every topic must have [Trending] or [Steady] tag
- Every item must be on its own separate line (no line merging)

## Trend Sources
- [Trending]: Google Trends (global), Reddit (r/personalfinance,
  r/investing, r/health, r/productivity, r/travel, r/artificial),
  Quora trending English questions, YouTube trending videos,
  X/Twitter popular tip threads → last 24~48 hours
- [Steady]: Google Autocomplete / People Also Ask (English),
  Answer the Public / AlsoAsked.com,
  Semrush/Ahrefs high-CPC English keywords,
  Reddit recurring beginner questions → last 6 months

## Title Generation Rules
- Character count: 45~65 characters in English
- Target keyword near the beginning
- Click-inducing patterns (choose most fitting):
  · Curiosity: "What Is [X]? A Simple Guide for Everyone"
  · Life benefit: "How [X] Can Save You Time Every Week"
  · Comparison: "[X] vs [Y]: Which One Should You Choose?"
  · Quick tip: "5 [X] Tips You'll Wish You Knew Sooner"
  · Beginner signals: "No Coding Needed", "Step-by-Step", "In 5 Minutes"
- Finance: No investment advice tone in title
- Health: No exaggerated claims in title

## Permalink Rules
- Lowercase English + hyphens only
- Max 60 characters
- Reflect core keyword of the article
- Example: "best-time-book-flights-2026"

## Article Structure (follow exactly)
1. Quick Summary Box (✅ 3 lines)
2. Relatable opening ("Have you ever wondered...?")
3. Image1
4. Core concept (analogy-first)
5. Main content (<ol><li>)
6. Comparison table (HTML table)
7. Image2
8. Real-life applications & pro tips
9. FAQ (minimum 3)
10. Image3
11. Conclusion (one specific next action)

## Tone & Voice
- Warm, clear, practical
- Real-world analogy BEFORE technical explanation (always)
- One mid-article engagement hook in own <p> tag
  Example: "Still with me? Good — here's where it gets useful."
- No robotic, academic, or hype language

## Anti-Hallucination Rules
- Only state rates, prices, statistics when certain
- Use hedged language when uncertain:
  "as of early 2026", "approximately", "check official site"
- No fabricated statistics or studies
- Only mention real, publicly available products and services
- Disclose uncertainty: "as of the time of writing"

## Category Disclaimers (mandatory)
- Finance: "This article is for informational purposes only
  and does not constitute financial advice."
- Health: "This article is for general informational purposes only.
  Consult a qualified healthcare professional."

## Meta Description
- 70~100 characters in English, max 100 strictly enforced

## Metadata Labels
Finance/Investing, Technology/AI, Health/Wellness,
Lifestyle/Productivity, Travel/Culture

## HTML Rules
- No H1 / H2: margin-top:32px / H3: margin-top:24px
- Max 2~3 sentences per paragraph
- No <p>&nbsp;</p> or standalone <br>
- Numbered lists: <ol><li> only
- Tables: HTML <table> only (no markdown pipes)
- Summary box: background:#f0f7ff; border-left:4px solid #0066cc
- Pro Tip box: background:#fff8e1; border-left:4px solid #f9a825
- Warning box: background:#fff3f3; border-left:4px solid #e53935
- Minimum 1,200 words