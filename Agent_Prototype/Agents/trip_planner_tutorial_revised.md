# Building Your Dream Vacation with TripPlanner: A Visual Guide

## Meet Your AI Travel Team 🧠

TripPlanner works like having four travel specialists collaborating on your perfect vacation:

```
┌─────────────────────────┐     ┌─────────────────────────┐
│                         │     │                         │
│  Destination Expert 🔍  │──►  │    Theme Curator 🎭     │
│  Analyzes locations     │     │  Creates story threads  │
│                         │     │                         │
└─────────────────────────┘     └─────────────────────────┘
             │                               │
             │                               │
             ▼                               ▼
┌─────────────────────────┐     ┌─────────────────────────┐
│                         │     │                         │
│ Itinerary Planner 📅    │◄─── │   Travel Concierge 💼   │
│ Builds daily schedule   │     │ Saves to Notion         │
│                         │     │                         │
└─────────────────────────┘     └─────────────────────────┘
```

## How It Creates Your Perfect Family Vacation

### Step 1: Share Your Family's Story 👨‍👩‍👦

I simply tell TripPlanner about my family:

```
"We're a family of 3 traveling to Netherlands & Belgium:
 - Wife: Loves art, museums, architecture
 - Husband: Enjoy history, science, food
 - Son(11 Yrs old): Fascinated by military history & science
 
We're traveling March 30-April 6, 2025, starting in Amsterdam, 
staying in Leiden (3 days), Bruges (1 day), and Delft (3 days)."
```

### Step 2: The Destination Expert Reveals Hidden Gems 🔍

Instead of generic tourist recommendations, the Destination Expert analyzes:

```
DESTINATION DECODING
│
├── The Netherlands (Early April)
│   ├── Cultural contradictions: Modern design vs. historic villages
│   ├── Seasonal exclusives: Early tulip season at Keukenhof
│   └── Key cities: Amsterdam, Leiden, Delft
│
├── Belgium (Early April)
│   ├── Cultural highlights: Medieval architecture, chocolate
│   ├── Military history: WWI battlefields near Bruges
│   └── Key cities: Bruges, Ghent
│
└── Family-Interest Mapping
    ├── For Son: Military sites, science museums, hands-on exhibits
    ├── For Wife (42): Art museums, architecture walks, cultural sites
    └── For Husband (40): Science centers, historical sites, culinary experiences
```

### Step 3: The Theme Curator Creates Meaningful Connections 🎭

Rather than disconnected tourist spots, the Theme Curator weaves experiences into cohesive journeys:

```
THEMATIC JOURNEYS
│
├── "Water Masters: The Liquid History of the Low Countries"
│   ├── Leiden's canal system
│   ├── Delft's water management history
│   ├── Bruges' medieval canals ("Venice of the North")
│   └── Rotterdam's innovative harbor and flood protection
│
├── "Scientific Pioneers: Laboratories of Innovation"
│   ├── Leiden University's scientific contributions
│   ├── TU Delft's cutting-edge research
│   ├── Naturalis Biodiversity Center
│   └── Hands-on science experiences for Son
│
├── "Strategic Significance: Military History Through Centuries"
│   ├── Medieval fortifications in Leiden and Bruges
│   ├── William of Orange's fight for independence
│   ├── WWI battlefields near Bruges
│   └── Interactive military history exhibits
│
└── Cross-Cutting Micro-Themes
    ├── Hidden Gems & Secret Passages
    ├── Hands-On Heritage (for Son)
    ├── Culinary Crossroads (for Husband)
    └── Urban Exploration & Nature Balance
```

### Step 4: The Itinerary Planner Creates Your Perfect Schedule 📅

Every day balances activities for each family member with practical details:

```
DAY 1 (Sunday, March 30) - ARRIVAL DAY IN LEIDEN
┌─────────┬───────────────────────────────┬─────────────────────────────┐
│  Time   │           Activity            │       Theme Connection      │
├─────────┼───────────────────────────────┼─────────────────────────────┤
│ Morning │ Arrive at Amsterdam Schiphol  │                             │
├─────────┼───────────────────────────────┼─────────────────────────────┤
│ 11:00AM │ Direct train to Leiden (20m)  │                             │
├─────────┼───────────────────────────────┼─────────────────────────────┤
│ 12:00PM │ Hotel check-in & lunch        │                             │
├─────────┼───────────────────────────────┼─────────────────────────────┤
│ 2:00PM  │ Leiden Canal Cruise (1 hour)  │ Water Masters               │
├─────────┼───────────────────────────────┼─────────────────────────────┤
│ 3:30PM  │ Burcht van Leiden (fort)      │ Strategic Significance      │
├─────────┼───────────────────────────────┼─────────────────────────────┤
│ 5:00PM  │ Leiden city orientation walk  │ Scientific Pioneers         │
├─────────┼───────────────────────────────┼─────────────────────────────┤
│ 7:00PM  │ Dinner at local restaurant    │                             │
└─────────┴───────────────────────────────┴─────────────────────────────┘

NOTES:
- The canal cruise introduces how water shaped Dutch cities
- The medieval fort offers Son his first glimpse of military history
- Light activities to ease into the trip after travel
```

### Step 5: Your Adventure is Saved and Ready to Go 💼

With one click, your complete itinerary is saved to Notion, with:
- Interactive Google Maps links
- Restaurant recommendations
- Backup plans for weather changes 
- Transportation details

## The Multi-Agent Magic Behind Your Perfect Trip 🪄

What makes TripPlanner powerful is how these AI agents collaborate through the langfun agentic action framework:

```
┌───────────────────────────────────────────────────────────┐
│                                                           │
│              TripAgent (Main Orchestrator)                │
│                                                           │
└───────────────┬───────────────────────┬───────────────────┘
                │                       │
                ▼                       ▼
┌───────────────────────┐   ┌───────────────────────┐
│                       │   │                       │
│  DestinationDecoding  │──►│   ThemeSynthesis      │
│        Agent          │   │      Agent            │
│                       │   │                       │
└───────────────────────┘   └──────────┬────────────┘
                                       │
                                       ▼
                           ┌───────────────────────┐
                           │                       │
                           │    PlannerAgent       │──┐
                           │                       │  │
                           └───────────────────────┘  │
                                                      │
                                                      ▼
                                      ┌───────────────────────┐
                                      │                       │
                                      │     ShareTrip         │
                                      │                       │
                                      └───────────────────────┘
```

Each agent:
1. Inherits from the langfun Action framework
2. Specializes in one aspect of travel planning
3. Can use different LLMs depending on the task
4. Passes results to the next agent in the sequence

The `allow_symbolic_assignment = True` property enables complex data to flow between agents, maintaining context throughout the planning process.

This multi-agent approach creates a vacation plan that feels handcrafted for your family - because it actually is!