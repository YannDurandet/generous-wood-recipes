"""Builds generous_wood.zip, a datapack that buffs vanilla wood recipes.
Edit the numbers in YIELD, then run: python build_generous_wood.py
Drop the zip in <world>/datapacks and run /reload."""
import json, os, zipfile

# RULE: no chain may burn longer per log than vanilla charcoal (1 log = 1600 ticks).
# Values below are the highest that respect it. Recipes only, plus one burn-time file (hanging signs).
# result counts (vanilla value in comment)
YIELD = {
    "stick": 8,          # 4
    "trapdoor": 8,       # 2
    "door": 12,          # 3
    "fence": 6,          # 3
    "fence_gate": 4,     # 1
    "sign": 12,          # 3
    "hanging_sign": 18,  # 6 (burn time lowered to 500 below, so 18 stays under the cap)
    "shelf": 18,         # 6
    "boat": 1,           # 1
    "button": 4,         # 1
    "pressure_plate": 2, # 1
    "slab": 6,           # 6
    "stairs": 8,         # 4
    "chest": 4,          # 1
    "barrel": 4,         # 1
    "ladder": 2,         # 3
    "bowl": 8,           # 4
    "mosaic_stairs": 8,  # 4
    "chiseled_bookshelf": 4, # 1
    "wood": 4,           # 3 (4 logs -> wood / stripped wood)
    "note_block": 4,     # 1
}

# wood name -> (planks, stripped log item)
WOODS = {w: (f"{w}_planks", f"stripped_{w}_log") for w in
         ["oak", "spruce", "birch", "jungle", "acacia", "dark_oak",
          "mangrove", "cherry", "pale_oak", "poplar"]}
WOODS["bamboo"] = ("bamboo_planks", "stripped_bamboo_block")
WOODS["crimson"] = ("crimson_planks", "stripped_crimson_stem")
WOODS["warped"] = ("warped_planks", "stripped_warped_stem")

STICK = "minecraft:stick"
CHAIN = "minecraft:iron_chain"

def shaped(pattern, key, result, count, cat):
    return {"type": "minecraft:crafting_shaped", "category": cat,
            "key": key, "pattern": pattern,
            "result": {"id": f"minecraft:{result}", "count": count}}

def shapeless(ings, result, count, cat):
    return {"type": "minecraft:crafting_shapeless", "category": cat,
            "ingredients": ings, "result": {"id": f"minecraft:{result}", "count": count}}

Y = YIELD
recipes = {}
for w, (planks, stripped) in WOODS.items():
    p = f"minecraft:{planks}"
    s = f"minecraft:{stripped}"
    recipes[f"{w}_trapdoor"] = shaped(["###", "###"], {"#": p}, f"{w}_trapdoor", Y["trapdoor"], "redstone")
    recipes[f"{w}_door"] = shaped(["##", "##", "##"], {"#": p}, f"{w}_door", Y["door"], "redstone")
    recipes[f"{w}_fence"] = shaped(["W#W", "W#W"], {"W": p, "#": STICK}, f"{w}_fence", Y["fence"], "misc")
    recipes[f"{w}_fence_gate"] = shaped(["#W#", "#W#"], {"#": STICK, "W": p}, f"{w}_fence_gate", Y["fence_gate"], "redstone")
    recipes[f"{w}_sign"] = shaped(["###", "###", " X "], {"#": p, "X": STICK}, f"{w}_sign", Y["sign"], "misc")
    recipes[f"{w}_hanging_sign"] = shaped(["C C", "###", "###"], {"C": CHAIN, "#": s}, f"{w}_hanging_sign", Y["hanging_sign"], "misc")
    recipes[f"{w}_shelf"] = shaped(["###", "   ", "###"], {"#": s}, f"{w}_shelf", Y["shelf"], "misc")
    recipes[f"{w}_button"] = shapeless([p], f"{w}_button", Y["button"], "redstone")
    recipes[f"{w}_pressure_plate"] = shaped(["##"], {"#": p}, f"{w}_pressure_plate", Y["pressure_plate"], "redstone")
    recipes[f"{w}_slab"] = shaped(["###"], {"#": p}, f"{w}_slab", Y["slab"], "building")
    recipes[f"{w}_stairs"] = shaped(["#  ", "## ", "###"], {"#": p}, f"{w}_stairs", Y["stairs"], "building")
    if w not in ("crimson", "warped"):
        boat = "bamboo_raft" if w == "bamboo" else f"{w}_boat"
        recipes[boat] = shaped(["# #", "###"], {"#": p}, boat, Y["boat"], "misc")

# logs -> wood blocks (bark on all sides), plain and stripped
for w in WOODS:
    if w == "bamboo":
        continue  # bamboo has no wood block
    stem = "stem" if w in ("crimson", "warped") else "log"
    hyph = "hyphae" if w in ("crimson", "warped") else "wood"
    recipes[f"{w}_{hyph}"] = shaped(["##", "##"], {"#": f"minecraft:{w}_{stem}"}, f"{w}_{hyph}", Y["wood"], "building")
    recipes[f"stripped_{w}_{hyph}"] = shaped(["##", "##"], {"#": f"minecraft:stripped_{w}_{stem}"}, f"stripped_{w}_{hyph}", Y["wood"], "building")

# tag-based recipes (one file covers every wood)
recipes["stick"] = shaped(["#", "#"], {"#": "#minecraft:planks"}, "stick", Y["stick"], "misc")
recipes["chest"] = shaped(["###", "# #", "###"], {"#": "#minecraft:planks"}, "chest", Y["chest"], "misc")
recipes["barrel"] = shaped(["PSP", "P P", "PSP"], {"P": "#minecraft:planks", "S": "#minecraft:wooden_slabs"}, "barrel", Y["barrel"], "misc")
recipes["ladder"] = shaped(["S S", "SSS", "S S"], {"S": STICK}, "ladder", Y["ladder"], "misc")
recipes["bowl"] = shaped(["# #", " # "], {"#": "#minecraft:planks"}, "bowl", Y["bowl"], "misc")
recipes["bamboo_mosaic_stairs"] = shaped(["#  ", "## ", "###"], {"#": "minecraft:bamboo_mosaic"}, "bamboo_mosaic_stairs", Y["mosaic_stairs"], "building")
recipes["note_block"] = shaped(["###", "#X#", "###"], {"#": "#minecraft:planks", "X": "minecraft:redstone"}, "note_block", Y["note_block"], "redstone")
recipes["chiseled_bookshelf"] = shaped(["###", "SSS", "###"], {"#": "#minecraft:planks", "S": "#minecraft:wooden_slabs"}, "chiseled_bookshelf", Y["chiseled_bookshelf"], "misc")

# The only burn-time change: hanging signs have their own burn-time file
# (nothing else shares it). Vanilla is 800; 18 per 6 logs x 500 = 1500 ticks/log <= 1600.
HANGING_SIGN_BURN = {
    "type": "minecraft:div", "left": 500,
    "right": {"type": "minecraft:conditional", "condition": "minecraft:block/fast_cooking",
              "on_false": "minecraft:cooking/normal_burn_time_reduction_factor",
              "on_true": "minecraft:cooking/fast_burn_time_reduction_factor"}}

mcmeta = {"pack": {"description": "Generous wood recipes",
                   "min_format": 121, "max_format": 121}}

with zipfile.ZipFile("generous_wood.zip", "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("pack.mcmeta", json.dumps(mcmeta, indent=2))
    if os.path.exists("pack.png"):  # pack icon shown in the in-game data pack list
        z.write("pack.png", "pack.png")
    for name, data in recipes.items():
        z.writestr(f"data/minecraft/recipe/{name}.json", json.dumps(data, indent=2))
    z.writestr("data/minecraft/context_int_provider/cooking/time_hanging_signs.json", json.dumps(HANGING_SIGN_BURN, indent=2))
print(f"{len(recipes)} recipes + 1 burn-time file written")
