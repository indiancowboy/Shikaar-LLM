"""Species catalog — the single list of species the app knows.

Each entry: (key, label, aliases, category, group). The key is what's stored on
freezer items (lowercase, underscores) — existing keys must never change, or
items already logged lose their match. Aliases are what people actually type;
the key (with spaces) and label are aliases automatically. Matching is by whole
word, longest alias first, so "snow goose" beats "goose", "mountain goat" beats
"goat", and "program" never matches anything.

The parser's fallback lexicon, its model prompt, and the UI's suggestions
(GET /species) are all generated from this list. Pure / offline.
"""
from __future__ import annotations

import re
from functools import lru_cache
from typing import NamedTuple, Optional


class Species(NamedTuple):
    key: str
    label: str
    aliases: tuple[str, ...]
    category: str
    group: str


# category -> (UI label, short description of what's in it)
CATEGORIES: dict[str, tuple[str, str]] = {
    "biggame": ("Big game", "lean: deer, elk, moose, sheep, antelope"),
    "hog": ("Hog / pork", "fatty: wild hog, javelina, domestic pork"),
    "bear": ("Bear", "fatty"),
    "smallgame": ("Small game", "rabbit, hare, squirrel, beaver"),
    "waterfowl": ("Waterfowl", "fatty: ducks, geese, crane"),
    "upland": ("Upland", "pheasant, quail, grouse, dove, wild turkey"),
    "poultry": ("Poultry", "chicken and other farm birds"),
    "redmeat": ("Red meat", "domestic: beef, lamb, goat"),
    "fishlean": ("Fish · lean", "redfish, walleye, cod, snapper"),
    "fishoily": ("Fish · oily", "salmon, trout, tuna, mackerel"),
    "shellfish": ("Shellfish", "crab, shrimp, lobster, clams"),
}

# Display order for the species picker. Groups are for browsing only; the
# category (shelf life, recipe matching) is set per species.
GROUPS: tuple[str, ...] = (
    "Big game", "Wild hog", "Bear", "Small game", "Waterfowl", "Upland",
    "Fish (lean)", "Fish (oily)", "Shellfish", "Domestic",
)

_RAW: list[tuple[str, str, list[str], str, str]] = [
    # ------------------------------------------------------------ big game ---
    ("whitetail", "Whitetail deer", ["whitetail deer", "white tail", "white-tailed deer", "deer", "venison"], "biggame", "Big game"),
    ("mule_deer", "Mule deer", ["muley", "muleys"], "biggame", "Big game"),
    ("blacktail_deer", "Blacktail deer", ["blacktail", "black-tailed deer", "sitka blacktail", "columbian blacktail"], "biggame", "Big game"),
    ("coues_deer", "Coues deer", ["coues"], "biggame", "Big game"),
    ("axis_deer", "Axis deer", ["axis", "chital"], "biggame", "Big game"),
    ("sika_deer", "Sika deer", ["sika"], "biggame", "Big game"),
    ("fallow_deer", "Fallow deer", ["fallow"], "biggame", "Big game"),
    ("red_deer", "Red deer", ["red stag"], "biggame", "Big game"),
    ("elk", "Elk", ["wapiti"], "biggame", "Big game"),
    ("moose", "Moose", [], "biggame", "Big game"),
    ("caribou", "Caribou", ["reindeer"], "biggame", "Big game"),
    ("antelope", "Pronghorn antelope", ["pronghorn"], "biggame", "Big game"),
    ("nilgai", "Nilgai", ["blue bull"], "biggame", "Big game"),
    ("blackbuck", "Blackbuck", ["blackbuck antelope"], "biggame", "Big game"),
    ("bison", "Bison", ["buffalo", "american bison"], "biggame", "Big game"),
    ("water_buffalo", "Water buffalo", [], "biggame", "Big game"),
    ("musk_ox", "Musk ox", ["muskox"], "biggame", "Big game"),
    ("mountain_goat", "Mountain goat", [], "biggame", "Big game"),
    ("wild_sheep", "Wild sheep", ["sheep"], "biggame", "Big game"),
    ("bighorn_sheep", "Bighorn sheep", ["bighorn", "desert bighorn", "rocky mountain bighorn"], "biggame", "Big game"),
    ("dall_sheep", "Dall sheep", ["dall"], "biggame", "Big game"),
    ("stone_sheep", "Stone sheep", [], "biggame", "Big game"),
    ("aoudad", "Aoudad", ["barbary sheep"], "biggame", "Big game"),
    ("mouflon", "Mouflon", [], "biggame", "Big game"),
    ("ibex", "Ibex", [], "biggame", "Big game"),
    ("tahr", "Tahr", ["himalayan tahr"], "biggame", "Big game"),
    ("chamois", "Chamois", [], "biggame", "Big game"),
    ("kudu", "Kudu", [], "biggame", "Big game"),
    ("impala", "Impala", [], "biggame", "Big game"),
    ("springbok", "Springbok", [], "biggame", "Big game"),
    ("oryx", "Oryx / gemsbok", ["gemsbok"], "biggame", "Big game"),
    ("eland", "Eland", [], "biggame", "Big game"),
    ("blesbok", "Blesbok", [], "biggame", "Big game"),
    ("wildebeest", "Wildebeest", ["gnu"], "biggame", "Big game"),
    # ------------------------------------------------------------ wild hog ---
    ("wild_hog", "Wild hog", ["hog", "hogs", "boar", "wild boar", "feral hog", "feral pig", "wild pig", "pig"], "hog", "Wild hog"),
    ("javelina", "Javelina", ["peccary", "collared peccary"], "hog", "Wild hog"),
    ("warthog", "Warthog", [], "hog", "Wild hog"),
    # ---------------------------------------------------------------- bear ---
    ("black_bear", "Black bear", ["bear"], "bear", "Bear"),
    ("brown_bear", "Brown bear / grizzly", ["grizzly", "grizzly bear", "kodiak bear"], "bear", "Bear"),
    # ---------------------------------------------------------- small game ---
    ("rabbit", "Rabbit", ["cottontail", "bunny"], "smallgame", "Small game"),
    ("hare", "Hare", ["snowshoe hare", "jackrabbit", "jack rabbit"], "smallgame", "Small game"),
    ("squirrel", "Squirrel", ["gray squirrel", "grey squirrel", "fox squirrel", "tree rat"], "smallgame", "Small game"),
    ("raccoon", "Raccoon", ["coon"], "smallgame", "Small game"),
    ("opossum", "Opossum", ["possum"], "smallgame", "Small game"),
    ("beaver", "Beaver", [], "smallgame", "Small game"),
    ("muskrat", "Muskrat", [], "smallgame", "Small game"),
    ("groundhog", "Groundhog", ["woodchuck"], "smallgame", "Small game"),
    ("nutria", "Nutria", [], "smallgame", "Small game"),
    # ----------------------------------------------------------- waterfowl ---
    ("duck", "Duck (mallard)", ["mallard", "ducks", "wild duck"], "waterfowl", "Waterfowl"),
    ("wood_duck", "Wood duck", ["woodie", "woodies"], "waterfowl", "Waterfowl"),
    ("teal", "Teal", ["green-winged teal", "blue-winged teal", "cinnamon teal"], "waterfowl", "Waterfowl"),
    ("pintail", "Pintail", [], "waterfowl", "Waterfowl"),
    ("gadwall", "Gadwall", [], "waterfowl", "Waterfowl"),
    ("wigeon", "Wigeon", ["widgeon", "baldpate"], "waterfowl", "Waterfowl"),
    ("shoveler", "Shoveler", ["spoonbill"], "waterfowl", "Waterfowl"),
    ("black_duck", "Black duck", [], "waterfowl", "Waterfowl"),
    ("mottled_duck", "Mottled duck", [], "waterfowl", "Waterfowl"),
    ("canvasback", "Canvasback", [], "waterfowl", "Waterfowl"),
    ("redhead", "Redhead", [], "waterfowl", "Waterfowl"),
    ("scaup", "Scaup / bluebill", ["bluebill", "bluebills", "lesser scaup", "greater scaup"], "waterfowl", "Waterfowl"),
    ("ringneck", "Ring-necked duck", ["ring-necked duck", "ringbill"], "waterfowl", "Waterfowl"),
    ("bufflehead", "Bufflehead", [], "waterfowl", "Waterfowl"),
    ("goldeneye", "Goldeneye", ["whistler"], "waterfowl", "Waterfowl"),
    ("merganser", "Merganser", [], "waterfowl", "Waterfowl"),
    ("eider", "Eider", [], "waterfowl", "Waterfowl"),
    ("scoter", "Scoter", [], "waterfowl", "Waterfowl"),
    ("goose", "Canada goose", ["canada goose", "honker", "honkers"], "waterfowl", "Waterfowl"),
    ("snow_goose", "Snow goose", ["blue goose", "ross's goose", "ross goose"], "waterfowl", "Waterfowl"),
    ("specklebelly", "Specklebelly goose", ["white-fronted goose", "specklebellies"], "waterfowl", "Waterfowl"),
    ("brant", "Brant", [], "waterfowl", "Waterfowl"),
    ("sandhill_crane", "Sandhill crane", ["crane"], "waterfowl", "Waterfowl"),
    ("coot", "Coot", [], "waterfowl", "Waterfowl"),
    # -------------------------------------------------------------- upland ---
    ("pheasant", "Pheasant", ["ringneck pheasant", "rooster pheasant"], "upland", "Upland"),
    ("quail", "Quail", ["bobwhite", "california quail", "gambel's quail", "scaled quail", "valley quail"], "upland", "Upland"),
    ("chukar", "Chukar", [], "upland", "Upland"),
    ("hungarian_partridge", "Hungarian partridge", ["hun", "huns", "gray partridge", "partridge"], "upland", "Upland"),
    ("ruffed_grouse", "Ruffed grouse", ["grouse", "partridge grouse"], "upland", "Upland"),
    ("sharptail", "Sharp-tailed grouse", ["sharp-tailed grouse", "sharptails"], "upland", "Upland"),
    ("sage_grouse", "Sage grouse", [], "upland", "Upland"),
    ("dusky_grouse", "Dusky / blue grouse", ["blue grouse"], "upland", "Upland"),
    ("spruce_grouse", "Spruce grouse", [], "upland", "Upland"),
    ("ptarmigan", "Ptarmigan", [], "upland", "Upland"),
    ("prairie_chicken", "Prairie chicken", [], "upland", "Upland"),
    ("dove", "Dove", ["mourning dove", "white-winged dove", "eurasian collared dove", "whitewing"], "upland", "Upland"),
    ("pigeon", "Pigeon / squab", ["squab"], "upland", "Upland"),
    ("woodcock", "Woodcock", ["timberdoodle"], "upland", "Upland"),
    ("snipe", "Snipe", [], "upland", "Upland"),
    ("turkey", "Wild turkey", ["wild turkey", "gobbler", "tom turkey"], "upland", "Upland"),
    # ------------------------------------------------------------ domestic ---
    ("chicken", "Chicken", ["chickens", "broiler", "fryer", "rooster"], "poultry", "Domestic"),
    ("cornish_hen", "Cornish hen", ["cornish game hen"], "poultry", "Domestic"),
    ("domestic_turkey", "Domestic turkey", ["store turkey", "farm turkey"], "poultry", "Domestic"),
    ("guinea_fowl", "Guinea fowl", ["guinea hen"], "poultry", "Domestic"),
    ("pekin_duck", "Pekin duck", ["pekin", "domestic duck", "muscovy"], "waterfowl", "Domestic"),
    ("beef", "Beef", ["steer", "ground beef"], "redmeat", "Domestic"),
    ("veal", "Veal", [], "redmeat", "Domestic"),
    ("lamb", "Lamb", [], "redmeat", "Domestic"),
    ("mutton", "Mutton", [], "redmeat", "Domestic"),
    ("goat", "Goat", ["chevon", "cabrito", "goat meat"], "redmeat", "Domestic"),
    ("pork", "Pork", ["domestic pork", "pork shoulder", "pork belly", "pork loin"], "hog", "Domestic"),
    # ----------------------------------------------------------- fish lean ---
    ("redfish", "Redfish", ["red fish", "red drum", "bull red"], "fishlean", "Fish (lean)"),
    ("black_drum", "Black drum", ["drum"], "fishlean", "Fish (lean)"),
    ("seatrout", "Speckled trout", ["speckled trout", "spotted seatrout", "sea trout", "speck", "specks", "weakfish"], "fishlean", "Fish (lean)"),
    ("flounder", "Flounder / fluke", ["fluke"], "fishlean", "Fish (lean)"),
    ("halibut", "Halibut", [], "fishlean", "Fish (lean)"),
    ("cod", "Cod", ["codfish", "pacific cod", "atlantic cod"], "fishlean", "Fish (lean)"),
    ("haddock", "Haddock", [], "fishlean", "Fish (lean)"),
    ("pollock", "Pollock", [], "fishlean", "Fish (lean)"),
    ("lingcod", "Lingcod", ["ling cod", "ling"], "fishlean", "Fish (lean)"),
    ("rockfish", "Rockfish", ["rock cod", "vermilion rockfish"], "fishlean", "Fish (lean)"),
    ("snapper", "Snapper", ["red snapper", "mangrove snapper", "vermilion snapper", "mutton snapper"], "fishlean", "Fish (lean)"),
    ("grouper", "Grouper", ["gag", "red grouper", "black grouper"], "fishlean", "Fish (lean)"),
    ("walleye", "Walleye", [], "fishlean", "Fish (lean)"),
    ("sauger", "Sauger", [], "fishlean", "Fish (lean)"),
    ("perch", "Perch", ["yellow perch"], "fishlean", "Fish (lean)"),
    ("crappie", "Crappie", ["slabs", "papermouth"], "fishlean", "Fish (lean)"),
    ("panfish", "Panfish", ["bluegill", "sunfish", "bream", "pumpkinseed"], "fishlean", "Fish (lean)"),
    ("bass", "Bass", ["largemouth", "largemouth bass", "smallmouth", "smallmouth bass", "black bass"], "fishlean", "Fish (lean)"),
    ("striped_bass", "Striped bass", ["striper", "stripers"], "fishlean", "Fish (lean)"),
    ("white_bass", "White bass", ["sand bass"], "fishlean", "Fish (lean)"),
    ("sea_bass", "Sea bass", ["black sea bass"], "fishlean", "Fish (lean)"),
    ("catfish", "Catfish", ["channel cat", "channel catfish", "blue catfish", "flathead", "flathead catfish", "bullhead"], "fishlean", "Fish (lean)"),
    ("pike", "Northern pike", [], "fishlean", "Fish (lean)"),
    ("muskie", "Muskie", ["musky", "muskellunge"], "fishlean", "Fish (lean)"),
    ("tilapia", "Tilapia", [], "fishlean", "Fish (lean)"),
    ("sheepshead", "Sheepshead", [], "fishlean", "Fish (lean)"),
    ("triggerfish", "Triggerfish", [], "fishlean", "Fish (lean)"),
    ("hogfish", "Hogfish", [], "fishlean", "Fish (lean)"),
    ("mahi", "Mahi-mahi", ["mahi mahi", "mahi-mahi", "dorado", "dolphinfish"], "fishlean", "Fish (lean)"),
    ("wahoo", "Wahoo", ["ono"], "fishlean", "Fish (lean)"),
    ("cobia", "Cobia", ["ling cobia"], "fishlean", "Fish (lean)"),
    ("tautog", "Tautog / blackfish", ["blackfish"], "fishlean", "Fish (lean)"),
    ("porgy", "Porgy / scup", ["scup"], "fishlean", "Fish (lean)"),
    ("tilefish", "Tilefish", [], "fishlean", "Fish (lean)"),
    ("whiting", "Whiting", [], "fishlean", "Fish (lean)"),
    ("sole", "Sole", ["petrale", "dover sole"], "fishlean", "Fish (lean)"),
    ("burbot", "Burbot", ["eelpout"], "fishlean", "Fish (lean)"),
    ("carp", "Carp", [], "fishlean", "Fish (lean)"),
    ("gar", "Gar", ["alligator gar"], "fishlean", "Fish (lean)"),
    ("sturgeon", "Sturgeon", [], "fishlean", "Fish (lean)"),
    # ----------------------------------------------------------- fish oily ---
    ("salmon", "Salmon", ["king salmon", "chinook", "coho", "silver salmon", "sockeye", "red salmon", "pink salmon", "humpy", "chum", "keta"], "fishoily", "Fish (oily)"),
    ("steelhead", "Steelhead", [], "fishoily", "Fish (oily)"),
    ("trout", "Trout", ["rainbow trout", "rainbow", "brook trout", "brookie", "brown trout", "cutthroat", "cutthroat trout"], "fishoily", "Fish (oily)"),
    ("lake_trout", "Lake trout", ["laker", "mackinaw"], "fishoily", "Fish (oily)"),
    ("arctic_char", "Arctic char", [], "fishoily", "Fish (oily)"),
    ("kokanee", "Kokanee", [], "fishoily", "Fish (oily)"),
    ("whitefish", "Lake whitefish", ["lake whitefish"], "fishoily", "Fish (oily)"),
    ("tuna", "Tuna", ["bluefin", "bluefin tuna", "yellowfin", "yellowfin tuna", "ahi", "albacore", "bigeye", "blackfin tuna", "skipjack"], "fishoily", "Fish (oily)"),
    ("bonito", "Bonito", [], "fishoily", "Fish (oily)"),
    ("mackerel", "Mackerel", ["spanish mackerel", "atlantic mackerel"], "fishoily", "Fish (oily)"),
    ("king_mackerel", "King mackerel", ["kingfish"], "fishoily", "Fish (oily)"),
    ("bluefish", "Bluefish", [], "fishoily", "Fish (oily)"),
    ("yellowtail", "Yellowtail / amberjack", ["amberjack", "hamachi", "yellowtail amberjack"], "fishoily", "Fish (oily)"),
    ("swordfish", "Swordfish", [], "fishoily", "Fish (oily)"),
    ("sablefish", "Sablefish / black cod", ["black cod", "butterfish"], "fishoily", "Fish (oily)"),
    ("shad", "Shad", [], "fishoily", "Fish (oily)"),
    ("herring", "Herring", [], "fishoily", "Fish (oily)"),
    ("sardine", "Sardines", ["sardines"], "fishoily", "Fish (oily)"),
    ("anchovy", "Anchovies", ["anchovies"], "fishoily", "Fish (oily)"),
    ("mullet", "Mullet", [], "fishoily", "Fish (oily)"),
    ("eel", "Eel", [], "fishoily", "Fish (oily)"),
    # ----------------------------------------------------------- shellfish ---
    ("crab", "Crab (Dungeness)", ["dungeness", "dungeness crab"], "shellfish", "Shellfish"),
    ("blue_crab", "Blue crab", [], "shellfish", "Shellfish"),
    ("king_crab", "King crab", [], "shellfish", "Shellfish"),
    ("snow_crab", "Snow crab", ["opilio"], "shellfish", "Shellfish"),
    ("stone_crab", "Stone crab", [], "shellfish", "Shellfish"),
    ("shrimp", "Shrimp / prawns", ["prawn", "prawns", "spot prawn", "spot prawns"], "shellfish", "Shellfish"),
    ("lobster", "Lobster", ["spiny lobster", "langosta"], "shellfish", "Shellfish"),
    ("crawfish", "Crawfish", ["crayfish", "crawdad", "crawdads", "mudbug", "mudbugs"], "shellfish", "Shellfish"),
    ("scallops", "Scallops", ["scallop", "bay scallops", "sea scallops"], "shellfish", "Shellfish"),
    ("clams", "Clams", ["clam", "razor clam", "razor clams", "quahog", "geoduck"], "shellfish", "Shellfish"),
    ("mussels", "Mussels", ["mussel"], "shellfish", "Shellfish"),
    ("oysters", "Oysters", ["oyster"], "shellfish", "Shellfish"),
    ("abalone", "Abalone", [], "shellfish", "Shellfish"),
    ("squid", "Squid / calamari", ["calamari"], "shellfish", "Shellfish"),
    ("octopus", "Octopus", [], "shellfish", "Shellfish"),
]

def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.lower().replace("_", " ").strip())


def _aliases(key: str, label: str, extra: list[str]) -> tuple[str, ...]:
    names = {_norm(key), _norm(label), *(_norm(a) for a in extra)}
    # Label variants like "Oryx / gemsbok" -> also each side on its own.
    for part in label.split("/"):
        names.add(_norm(re.sub(r"\(.*?\)", "", part)))
    # Geese: "snow goose" -> "snow geese".
    names |= {n[:-5] + "geese" for n in names if n.endswith("goose")}
    return tuple(sorted(n for n in names if n))


@lru_cache(maxsize=1)
def catalog() -> tuple[Species, ...]:
    return tuple(Species(k, label, _aliases(k, label, extra), cat, grp) for k, label, extra, cat, grp in _RAW)


@lru_cache(maxsize=1)
def _index() -> tuple[dict[str, Species], list[tuple[str, Species, re.Pattern]]]:
    by_key = {s.key: s for s in catalog()}
    alias_list = []
    for s in catalog():
        for a in s.aliases:
            # whole word, optional plural (s / es)
            pat = re.compile(r"\b" + re.escape(a) + r"(?:e?s)?\b")
            alias_list.append((a, s, pat))
    alias_list.sort(key=lambda x: len(x[0]), reverse=True)  # longest first
    return by_key, alias_list


def by_key(key: str) -> Optional[Species]:
    return _index()[0].get(key)


def lookup(text: str) -> Optional[Species]:
    """Best species for a name or phrase: exact key, else the longest alias
    found as a whole word ("bull elk" -> elk, "snow geese" -> snow_goose)."""
    if not text:
        return None
    t = _norm(text)
    keyed = by_key(t.replace(" ", "_"))
    if keyed:
        return keyed
    for _, s, pat in _index()[1]:
        if pat.search(t):
            return s
    return None


def find_all(text: str) -> list[tuple[int, Species]]:
    """Every non-overlapping species mention in `text`, in reading order.
    Longest aliases claim their span first."""
    t = text.lower()
    used = [False] * len(t)
    hits: list[tuple[int, Species]] = []
    for _, s, pat in _index()[1]:
        for m in pat.finditer(t):
            if any(used[m.start():m.end()]):
                continue
            for j in range(m.start(), m.end()):
                used[j] = True
            hits.append((m.start(), s))
    hits.sort(key=lambda h: h[0])
    return hits


def prompt_category_map() -> str:
    """Compact "category: species keys" lines for the extraction prompt."""
    lines = []
    for cat in CATEGORIES:
        keys = [s.key for s in catalog() if s.category == cat]
        lines.append(f"{cat}: {', '.join(keys)}")
    return "\n".join(lines)
