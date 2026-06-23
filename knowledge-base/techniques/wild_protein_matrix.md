---
title: "Wild Protein Cooking Matrix"
slug: "wild_protein_matrix"
doc_type: "routing_matrix"
version: "1.0"
description: "Master routing document connecting wild proteins → cuts → techniques → cuisines. This is Shikaar's primary decision layer for cooking recommendations."
proteins_covered:
  - venison
  - wild_boar
  - waterfowl
  - upland_birds
  - firm_white_fish
  - pelagic_fish
cuisines_referenced:
  - kashmir
  - punjab
  - rajasthan
  - agra_delhi
  - awadh
  - bengal
  - hyderabad
  - tamil_nadu
  - kerala
  - western_coast
  - tribal_india
  - trans_himalayan
  - north_northeast_india
tags:
  - routing
  - protein-pairing
  - technique-matching
  - cuisine-selection
---

# Wild Protein Cooking Matrix

This document is Shikaar's primary routing layer. When a user asks "I have [protein], what should I make?", this matrix provides the decision logic connecting:

**Protein → Cut → Technique → Cuisine**

Each section includes species-specific notes that generic LLMs cannot reliably provide.

---

## Section 1: Venison (Whitetail, Mule Deer, Axis, Elk, Fallow, Blacktail)

Venison is lean, clean-flavored, and versatile. The primary variables are:
- **Fat palatability** (species-dependent)
- **Cut location** (determines technique)
- **Age of animal** (affects tenderness and flavor intensity)

### Cut Matrix

| Cut | Characteristics | Best Techniques | Cuisine Matches | Watch Out For | Fat Addition? |
|-----|-----------------|-----------------|-----------------|---------------|---------------|
| **Backstrap / Loin** | Lean, tender, premium, minimal connective tissue | Hot sear (medium-rare), dry masala fry, tataki, carpaccio | Bengali (mustard sear), Tamil Nadu (pepper fry), Rajasthan (dry masala), Kerala (pepper fry), Tribal (fire roast) | Overcooking—loses moisture fast above medium; wet braises waste this cut | Yes, cook in ghee/butter |
| **Tenderloin** | Very lean, extremely tender, small | Quick sear, carpaccio, tataki, minimal cooking | Bengali (light mustard), Awadh (delicate kebab), Trans-Himalayan (butter sear) | Any long cooking destroys it; don't marinate acidic for long | Yes, butter/ghee finish |
| **Shoulder** | Tough, connective tissue, rich flavor when braised | Long braise (2-4 hrs), grind, stew | Rajasthan (lal maas), Kashmir (rogan josh style), Hyderabad (tangy braise), Punjab (slow curry), Kerala (coconut braise), North/Northeast (bamboo shoot stew) | Undercooking—needs full collagen breakdown; no added fat if braising in ghee-rich sauce | Depends on method |
| **Neck** | Very tough, collagen-rich, intense flavor | Braise 3+ hrs, osso buco style, stock | Awadh (nihari-style), Kashmir (slow braise), Hyderabad (haleem), Trans-Himalayan (barley stew) | Impatience—this cut needs time; excellent for ground if braising isn't feasible | No if braising |
| **Shanks** | Tough, bone-in, collagen-heavy | Braise until falling off bone, soup/stock | Kashmir (wazwan-style), Awadh (nihari), Hyderabad (paya-style), Trans-Himalayan (mountain stew) | Needs full collagen breakdown—3+ hours minimum | No if braising |
| **Ribs** | Thin, minimal meat, mostly bone | Braise, soup stock, slow smoke | North/Northeast (smoked broth), Trans-Himalayan (stew), Tribal (fire roast) | Don't expect beef rib yield—use for flavor extraction | No |
| **Trim / Scraps** | Variable quality, mix of lean and sinew | Grind (add 15-20% fat), sausage, keema | Any cuisine—ground is versatile: Agra/Delhi (kebabs), Awadh (galouti), Rajasthan (keema), Punjab (keema paratha) | Must add fat to grind or it's dry and crumbly | Yes, 15-20% pork/beef fat |
| **Heart** | Dense, lean, mineral-rich, mild organ flavor | Quick sear (medium-rare), skewer, slice thin | Rajasthan (dry masala), Tamil Nadu (pepper fry), Tribal (fire roast), Punjab (tandoor skewer) | Overcooking—treat like a lean steak; remove valves and fat cap | Yes, cook in fat |
| **Liver** | Strong flavor, soft texture, iron-rich | Quick sear, pâté, flash fry | Bengal (light fry), Punjab (masala fry), Tribal (fire roast) | Overcooking turns chalky; don't serve to those sensitive to organ flavor | Yes, butter/ghee |

### Species-Specific Notes

**Axis Deer**
- Fat is palatable—keep some in braises and grinds
- Mild, slightly sweet flavor
- Forgiving to cook; good beginner venison

**Whitetail**
- Trim fat aggressively—it's tallowy and coats the mouth
- Compensate with added pork or beef fat in grinds
- Rutting bucks can have stronger flavor; brine or marinate

**Mule Deer**
- Similar to whitetail; trim fat
- Sage-country deer may have herbal notes from diet
- Generally mild when properly handled

**Elk**
- Very lean, very mild, almost beef-like
- Larger cuts—plan processing space
- Excellent for beginners; forgiving flavor profile

**Fallow Deer**
- Farm-raised fallow is mild; wild can vary
- Fat is moderate—taste before deciding to trim
- Good all-around venison

---

## Section 2: Wild Boar / Feral Hog

Wild boar is richer and leaner than domestic pork, with more assertive flavor. Key considerations:
- **Age and size** (younger = milder, older = stronger)
- **Sex and season** (boars in rut have stronger flavor)
- **Trichinella risk** (cook to 160°F or freeze per USDA guidelines in endemic areas)

### Cut Matrix

| Cut | Characteristics | Best Techniques | Cuisine Matches | Watch Out For | Fat Addition? |
|-----|-----------------|-----------------|-----------------|---------------|---------------|
| **Loin / Backstrap** | Leaner than domestic, mild to moderate flavor | Sear, roast, dry rub, quick cook | Rajasthan (dry masala), Punjab (tandoor), Tamil Nadu (pepper fry), Kerala (pepper fry) | Overcooking—dries out faster than domestic pork; brine helps | Sometimes—brine or bacon wrap |
| **Shoulder** | Tough, fatty (but less than domestic), rich | Long braise, carnitas, pulled, ground | Rajasthan (lal maas), Western Coast (vindalho, xacuti), Kashmir (rogan josh style), Hyderabad (tangy braise), North/Northeast (bamboo stew) | Can be greasy if not trimmed; old boars need longer cook times | No—has internal fat |
| **Ribs** | More meat than deer ribs, good fat marbling | Smoke low-and-slow, braise, St. Louis style | Punjab (tandoor), Tamil Nadu (Chettinad), Tribal (fire roast), North/Northeast (smoked) | Still less meat than domestic pork ribs; young pigs have smaller racks | No |
| **Belly** | Variable—young pigs may have little belly | Cure (bacon), braise, crispy preparation | Western Coast (Goan-style), Punjab (slow cook), Bengal (mustard braise) | Size varies dramatically by animal; may not be worth saving on small pigs | No |
| **Leg / Ham** | Large, lean-ish, good for roasts or cured | Roast whole, cure (prosciutto-style), braise | Kashmir (slow roast), Agra/Delhi (Mughal roast), Trans-Himalayan (simple roast) | Needs brining or barding for roasts; curing requires experience | Yes for roasts |
| **Trim / Scraps** | Rich, variable fat content | Sausage, grind, keema | Any—boar makes excellent sausage: Western Coast (Goan sausage style), Punjab (keema), Rajasthan (spiced keema) | Balance fat content in grind—may need less added fat than venison | Check fat % |
| **Jowl / Cheeks** | Fatty, collagen-rich, intense flavor | Cure (guanciale), braise until tender | Western Coast (vindalho), Awadh (slow braise), Italian-adjacent preparations | Small yield; worth saving for charcuterie or special braises | No |

### Species-Specific Notes

**Feral Hogs (US)**
- Highly variable—corn-fed hogs are milder, rooting hogs can be stronger
- Young pigs (under 100 lbs) are milder and more versatile
- Old boars, especially in rut, benefit from brining or aggressive spicing

**European Wild Boar**
- Generally more consistent flavor than US ferals
- Often acorn-fed, which produces excellent fat
- Leg is prized for curing

**Trichinella Considerations**
- In endemic areas, cook to 160°F internal
- Alternatively, freeze per USDA guidelines (specific time/temp varies)
- Not all regions have trichinella risk—know your area

---

## Section 3: Waterfowl (Duck, Goose)

Waterfowl have rich, red meat and significant fat deposits. Key considerations:
- **Puddle ducks vs. divers** (divers can taste fishy)
- **Fat rendering** (don't discard—it's premium cooking fat)
- **Breast vs. legs** (different cook times and methods)

### Cut Matrix

| Cut | Characteristics | Best Techniques | Cuisine Matches | Watch Out For | Fat Addition? |
|-----|-----------------|-----------------|-----------------|---------------|---------------|
| **Breast** | Rich, red meat, fat cap, best medium-rare | Score skin and sear, smoke, cure (pastrami), tataki | Rajasthan (dry masala), Bengal (mustard sear), Tamil Nadu (pepper fry), Kashmir (saffron-spiced), Punjab (tandoor) | Overcooking—should be pink inside; score fat cap to render | No—has fat cap |
| **Legs / Thighs** | Tough, sinewy, rich flavor | Confit (2+ hrs in fat), long braise, red braise | Kashmir (slow braise), Rajasthan (lal maas style), Kerala (coconut braise), Western Coast (vindalho), North/Northeast (smoked stew) | Need 2+ hours to become tender; don't rush | No—confit in own fat |
| **Fat** | Liquid gold—renders clean, high smoke point | Render and save for cooking | Any cuisine that uses cooking fat | Don't discard; store rendered fat in fridge for months | N/A |
| **Liver** | Rich, buttery, classic for pâté | Sear quickly, pâté, mousse | Awadh (delicate prep), Bengal (quick fry), Punjab (masala fry) | Overcooking—should be pink inside; strong flavor for some palates | Yes, butter |
| **Gizzards / Hearts** | Dense, chewy, mineral flavor | Confit until tender, slice thin and sear, skewer | Tamil Nadu (pepper fry), Punjab (tandoor skewer), Tribal (fire roast) | Gizzards need long cooking to tenderize; hearts are quick-cook | Depends on method |

### Species-Specific Notes

**Mallard**
- Most versatile, mild for a duck
- Good starting point for waterfowl cookery
- Fat renders well

**Teal**
- Small—often cook whole or just harvest breasts
- Clean, mild flavor
- Quick cooking due to size

**Goose**
- Larger, more fat, longer cook times on legs
- Excellent fat yield for rendering
- Breast can be quite large—treat like a small roast

**Diver Ducks (Bluebill, Canvasback, etc.)**
- Can taste fishy depending on diet
- Brine heavily (12-24 hrs) with aromatics
- Use strong spices: Rajasthan, Tamil Nadu, Western Coast
- Some hunters only use divers for sausage

**Puddle Ducks (Mallard, Pintail, Wigeon)**
- Generally cleaner flavor than divers
- More versatile in cuisine pairing
- Fat is premium quality

---

## Section 4: Upland Birds (Pheasant, Quail, Dove, Chukar, Grouse)

Upland birds are lean, delicate, and quick-cooking. Primary concerns:
- **Size** (determines whole vs. parted cooking)
- **Breast vs. leg timing** (breasts dry before legs finish)
- **Diet influence** (sage grouse, for example, can be herbal)

### Cut Matrix

| Cut | Characteristics | Best Techniques | Cuisine Matches | Watch Out For | Fat Addition? |
|-----|-----------------|-----------------|-----------------|---------------|---------------|
| **Whole Bird** | Lean, delicate, quick-cooking | Roast, spatchcock, grill, tandoor | Rajasthan (Rajput hunter style), Punjab (tandoor), Kashmir (aromatic roast), Tribal (fire roast) | Breast dries before legs finish—consider separating or spatchcocking | Yes—bard or baste |
| **Breast** | Very lean, mild, quick-cook | Quick sear, sous vide, bacon-wrap, pan sauce | Bengal (mustard sear), Tamil Nadu (pepper fry), Awadh (delicate kebab), Kerala (quick fry) | Overcooking is the #1 failure—should be slightly pink; rest before slicing | Yes—cook in fat, bard with bacon |
| **Legs / Thighs** | Tougher, more flavor | Confit, braise, crispy fry | Kashmir (slow braise), Western Coast (xacuti), Kerala (coconut braise), Rajasthan (dry braise) | Undercooked = chewy; consider cooking separately from breast | Depends on method |

### Species-Specific Notes

**Pheasant**
- Largest common upland bird, most forgiving
- Can roast whole successfully
- Mild, slightly gamey flavor

**Quail**
- Tiny—cook whole, often grilled or fried
- Cooks in minutes
- Very mild, almost chicken-like

**Dove**
- Small, dark meat, lean
- Often just harvest breasts (poppers)
- Wrap in bacon or cook in fat—very lean

**Chukar**
- Medium-sized, legs are notably tough
- Consider separating breast and legs for different treatments
- Clean, mild flavor

**Grouse (including Sage Grouse)**
- Can have strong, herbal flavor depending on diet
- Sage grouse especially can be challenging—brine if sage-heavy
- Smaller species like ruffed grouse are milder

---

## Section 5: Firm White Fish (Rockfish, Lingcod, Halibut, Striped Bass)

Firm white fish have mild flavor and sturdy texture that holds up to various cooking methods. Key considerations:
- **Freshness** (fish degrades faster than meat)
- **Skin on vs. off** (affects technique choice)
- **Thickness** (determines cook time)

### Cut Matrix

| Cut | Characteristics | Best Techniques | Cuisine Matches | Watch Out For | Fat Addition? |
|-----|-----------------|-----------------|-----------------|---------------|---------------|
| **Fillet (skin-on)** | Sturdy, mild, versatile | Pan sear (crispy skin), grill, bake | Bengal (mustard curry), Kerala (moilee, fish fry), Tamil Nadu (fish fry), Western Coast (Konkani fry) | Overcooking—fish is done when it flakes; skin should crisp, not steam | Yes—cook in oil/ghee |
| **Fillet (skinless)** | Clean, mild, delicate | Poach, curry, steam, pan sear | Kerala (coconut curry), Bengal (shorshe), Awadh (delicate korma), Kashmir (yogurt broth) | More delicate than skin-on; handle gently; don't overcook | Yes for searing |
| **Steak (bone-in)** | Sturdy, good for grilling, even cooking | Grill, tandoor, pan roast | Punjab (tandoor), Rajasthan (dry masala), Hyderabad (tangy curry), Tamil Nadu (fish curry) | Bone-in takes slightly longer; check near bone for doneness | Yes for grilling |
| **Whole (small fish)** | Presentation, even cooking, bones add flavor | Roast, grill, fry, steam | Tribal (fire roast, leaf wrap), Bengal (whole fish fry), Kerala (whole fish curry), Western Coast (recheado) | Score skin for even cooking; stuff cavity with aromatics | Yes—baste or stuff with fat |
| **Collar** | Fatty, rich, often discarded but prized | Grill, broil, salt-bake | Tamil Nadu (grilled with spice), Punjab (tandoor), Western Coast (Goan-style grill) | Don't overcook—fat keeps it moist; one of the best parts | No—naturally fatty |
| **Cheeks** | Small, tender, sweet, often discarded | Quick sear, tempura, ceviche | Bengal (quick fry), Kerala (fish fry), Awadh (delicate treatment) | Tiny—need multiple fish to get a portion; don't overcook | Yes |

### Species-Specific Notes

**Halibut**
- Very lean, large flakes, premium texture
- Dries out easily—don't overcook
- Cheeks are a delicacy

**Lingcod**
- Firm, slightly blue-green raw (normal), turns white when cooked
- Excellent texture for curries and grilling
- Forgiving to cook

**Rockfish**
- Variable species, generally mild and medium-firm
- Good all-purpose white fish
- Skin crisps well

**Striped Bass**
- Mild, slightly sweet, medium-firm
- Excellent for Bengali preparations
- Good fat content for a white fish

---

## Section 6: Pelagic Fish (Tuna, Yellowtail, Bonito, Mahi, Wahoo)

Pelagic fish are often richer, with more assertive flavor and varying fat content. Key considerations:
- **Fat content** (varies by species and cut)
- **Serving temperature** (many are excellent raw or rare)
- **Bleeding and handling** (critical for quality)

### Cut Matrix

| Cut | Characteristics | Best Techniques | Cuisine Matches | Watch Out For | Fat Addition? |
|-----|-----------------|-----------------|-----------------|---------------|---------------|
| **Loin (sashimi-grade)** | Rich, clean, best raw or rare | Sashimi, tataki, quick sear (rare), crudo | Minimal preparation best; Bengal (light mustard sear), Tamil Nadu (pepper sear—rare) | Overcooking destroys the point—serve rare or raw; quality depends on bleeding/handling | No |
| **Loin (cooking-grade)** | Slightly less pristine, still excellent | Sear (medium-rare to medium), grill, curry | Tamil Nadu (pepper sear), Rajasthan (dry masala—don't overcook), Kerala (fish curry), Western Coast (recheado) | Still don't overcook—medium at most for tuna/yellowtail | Sometimes—depends on species |
| **Belly (toro, etc.)** | Very fatty, rich, melt-in-mouth | Sashimi, quick sear, tataki | Best with minimal treatment; light Bengali mustard sear | Overcooking wastes the fat; this is premium—don't drown in spice | No—very fatty |
| **Steak (bone-in)** | Sturdy, good for grilling | Grill, tandoor, pan roast | Punjab (tandoor), Hyderabad (tangy curry), Western Coast (Goan-style) | Bone-in takes longer; mahi and wahoo can dry out—watch closely | Sometimes |
| **Collar** | Fatty, rich, prized cut | Grill, broil, salt-bake | Tamil Nadu (spiced grill), Punjab (tandoor), minimal preparations | Don't overcook—one of the best parts of the fish | No—fatty |
| **Trim / Scraps** | Variable quality | Poke, tartare, fish cakes, curry | Bengal (fish cakes), Kerala (fish curry), Western Coast (fish curry) | Quality varies—taste before deciding on raw vs. cooked application | Depends on use |

### Species-Specific Notes

**Yellowfin / Ahi Tuna**
- Best rare to medium-rare
- Loin is sashimi-grade if properly handled
- Collar and belly are prized

**Yellowtail (Hamachi)**
- Rich, buttery, excellent raw
- Belly (hamachi belly) is very fatty
- Collar is exceptional grilled

**Bonito / Skipjack**
- Stronger flavor than other tunas
- Good for smoking, curing (katsuobushi)
- Can handle bolder spices—Tamil Nadu, Rajasthan work well

**Mahi Mahi**
- Leaner than tuna, firmer texture
- Good for grilling and curries
- Can dry out—don't overcook

**Wahoo (Ono)**
- Very lean, very firm, mild
- Dries out easily—cook carefully
- Good for ceviche, quick sear

---

## SHIKAAR_ROUTING_LOGIC

### Primary Decision Tree

```
1. IDENTIFY PROTEIN
   └── What animal/fish?
       └── Route to appropriate section

2. IDENTIFY CUT
   └── What part of the animal?
       └── Match to cut row in matrix

3. MATCH TECHNIQUE TO CUT
   └── Tender/quick-cook cuts → fast techniques
   └── Tough/connective tissue cuts → braise/slow techniques
   └── Fatty cuts → can handle dry heat
   └── Lean cuts → need added fat or careful temp control

4. MATCH CUISINE TO TECHNIQUE + USER PREFERENCE
   └── User wants heat → Rajasthan, Tamil Nadu, Western Coast
   └── User wants mild/aromatic → Kashmir, Awadh, Trans-Himalayan
   └── User wants coconut → Kerala, Western Coast
   └── User wants mustard → Bengal
   └── User wants tandoor/smoky → Punjab, Tribal
   └── User wants tangy/sour → Hyderabad, Western Coast, Tamil Nadu
   └── User wants simple/rustic → Tribal, Trans-Himalayan
   └── User wants fermented/smoked → North/Northeast
```

### Negative Routing (When NOT to Recommend)

| Cuisine | Avoid When... |
|---------|---------------|
| Rajasthan | User wants mild food; delicate fish that will be buried by heat |
| Kashmir | User wants very spicy; quick-cook preparations |
| Awadh | User wants bold, rustic flavors; quick preparations |
| Bengal | User wants creamy/coconut; very spicy |
| Tamil Nadu | User wants mild; coconut-heavy |
| Kerala | User wants dry preparations; no coconut |
| Western Coast | User wants mild; no vinegar/tang |
| Punjab | User wants subtle; no tomato-cream |
| Hyderabad | User wants very simple; no tang |
| Tribal | User wants refined; complex spicing |
| Trans-Himalayan | User wants bold spice; complex preparations |
| North/Northeast | User wants familiar Indian flavors; no fermented/bamboo |

---

## Quick Reference: Cuisine by Heat Level

| Heat Level | Cuisines |
|------------|----------|
| **Low** | Trans-Himalayan, Tribal, Awadh |
| **Low-Medium** | Kashmir, Bengal |
| **Medium** | Punjab, Agra/Delhi, North/Northeast |
| **Medium-High** | Kerala, Tamil Nadu, Hyderabad, Western Coast |
| **High** | Rajasthan, Chettinad (Tamil Nadu) |

---

## Quick Reference: Cuisine by Primary Fat

| Fat | Cuisines |
|-----|----------|
| **Ghee-dominant** | Rajasthan, Punjab, Kashmir, Awadh, Agra/Delhi |
| **Mustard oil** | Bengal, Kashmir (everyday) |
| **Coconut oil** | Kerala, Western Coast, Tamil Nadu |
| **Minimal fat** | Tribal, Trans-Himalayan, North/Northeast |

---

## Quick Reference: Cuisine by Technique Strength

| Technique | Best Cuisines |
|-----------|---------------|
| **Long braise** | Kashmir, Rajasthan, Awadh, Hyderabad, Western Coast |
| **Quick sear/fry** | Bengal, Tamil Nadu, Kerala, Rajasthan |
| **Tandoor/grill** | Punjab, Rajasthan, Tribal |
| **Coconut curry** | Kerala, Western Coast |
| **Yogurt-based** | Kashmir, Awadh, Punjab |
| **Dry masala** | Rajasthan, Tamil Nadu |
| **Smoked/fermented** | North/Northeast, Tribal |
| **Simple stew** | Trans-Himalayan, Tribal |
