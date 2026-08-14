from __future__ import annotations

ABILITY_FACTS_NOTE = (
    "ability_facts are authoritative hero mechanics for this lobby. Prefer them "
    "over memory. Do not invent interactions that are not listed here or in the "
    "general spell rules."
)

FACTS: dict[str, list[str]] = {
    "Bane": [
        "Enfeeble reduces attack damage and cast range. It does not reduce spell damage.",
        "Fiend's Grip and Nightmare are hard disables. Do not ask for Enfeeble on a Gripped or Nightmared target; Enfeeble into Nightmare wastes the debuff duration.",
        "Nightmare transfers on attack and breaks on damage. It is also a save or a setup, not only a disable.",
    ],
    "Zeus": [
        "Static Field damages on every Zeus cast around him; high cast counts are the point of the hero.",
        "Thundergods Wrath hits all visible enemy heroes and reveals invisible ones near the strike, and Nimbus casts Lightning Bolt from anywhere.",
        "Heavenly Jump is his only escape; Zeus dying while it is available is a positioning error, not a hero weakness.",
    ],
    "Shadow Fiend": [
        "Necromastery souls are lost on death: half the stacks. Early deaths on SF cost damage as well as gold.",
        "Requiem of Souls damage scales with souls, so a starved SF ults for little.",
    ],
    "Drow Ranger": [
        "Marksmanship is disabled when an enemy hero is within 400 range; standing on Drow turns off her damage.",
        "Gust is her only disable and self-peel; when it is down she is killable.",
    ],
    "Shadow Shaman": [
        "Hex and Shackles together are one of the longest solo lockdowns in the game, but Shackles is a channel that Shaman must stand still for.",
        "Mass Serpent Wards is a tower-killing ultimate; a dead Shaman near your tower saved a building.",
    ],
    "Crystal Maiden": [
        "Frostbite roots and damages but does not silence; the target can still cast.",
        "Freezing Field is a channel that ends on any hard disable.",
    ],
    "Witch Doctor": [
        "Paralyzing Cask stuns bounce; clumping against WD extends the disable.",
        "Death Ward is a channel; killing or disabling WD ends it.",
    ],
    "Dazzle": [
        "Shallow Grave prevents death but not damage; burst through it ends when it expires, so kill confirm needs timing, not more damage inside the Grave.",
    ],
    "Dawnbreaker": [
        "Solar Guardian is a global teleport heal; counting Dawnbreaker as absent because she is on another lane is wrong once she has her ultimate.",
    ],
    "Ursa": [
        "Fury Swipes stack per hit; extended trades favor Ursa. Short disables and kiting beat him, long trades do not.",
        "Enrage reduces incoming damage and can be cast while disabled.",
    ],
    "Undying": [
        "Decay steals strength per cast in lane; a laner sitting in Decay range bleeds max HP.",
        "Tombstone zombies slow; the fight rule is kill the Tombstone first.",
    ],
    "Spectre": [
        "Haunt sends an illusion to every enemy hero globally; Spectre joins fights she is not standing in.",
        "Dispersion reflects damage; bursting a tanky Spectre hurts the attackers.",
    ],
    "Tusk": [
        "Snowball makes allies inside untargetable during the roll; it is a save as well as an engage.",
        "Walrus Punch is a guaranteed crit that launches the target.",
    ],
    "Lina": [
        "Fiery Soul stacks attack and move speed on casts; Lina after a fight opener is faster than she looks.",
        "Laguna Blade with Aghanim's Scepter deals pure damage and pierces spell immunity.",
    ],
    "Phantom Assassin": [
        "Blur gives evasion; magic damage and evasion piercing (MKB) are the counters.",
        "Coup de Grace crits are the kill condition; disarms and Enfeeble-type attack debuffs blunt her.",
    ],
    "Silencer": [
        "Global Silence is global; fights started inside it are fought without spells.",
        "Glaives of Wisdom steal intelligence on kills near him.",
    ],
    "Underlord": [
        "Fiend's Gate is a team teleport; Underlord's team can show anywhere on the map late game.",
        "Atrophy Aura reduces attack damage of nearby enemies.",
    ],
    "Muerta": [
        "Dead Shot's fear turns the target away; it is a soft disable, not a stun.",
        "Pierce the Veil converts her attacks to magic damage; BKB-style spell immunity blanks her during it.",
    ],
    "Luna": [
        "Eclipse damage is heavy burst at night or with setup; Lucent Beam is a mini stun with Aghanim's Scepter.",
    ],
    "Skywrath Mage": [
        "Ancient Seal amplifies magic damage and silences; it marks the kill target.",
        "Mystic Flare deals its damage split among heroes in the zone; solo targets take it all.",
    ],
    "Legion Commander": [
        "Duel is a mutual disarm-and-fight; wins grant permanent damage. A Duel into enemy backup is a throw, not bad luck.",
        "Press the Attack dispels and heals; it answers silences and roots.",
    ],
    "Pudge": [
        "Meat Hook pulls the first unit hit, ally or enemy; creeps body-blocking hooks is real counterplay.",
        "Dismember is a channel that heals Pudge while it runs.",
    ],
    "Kunkka": [
        "Torrent and Ghostship have long lead times; they need setup or the enemy dodges.",
        "X Marks the Spot returns the target to the mark; it sets up Torrent and cancels TPs.",
    ],
    "Faceless Void": [
        "Chronosphere freezes everyone inside including allies; fighting into it without the counter engage loses the fight.",
        "Time Walk undoes recent damage; burst him after Time Walk, not before.",
    ],
    "Enigma": [
        "Black Hole is a channel and a hard disable; it is the fight, and cancelling it wins the fight.",
    ],
}


def facts_for_heroes(hero_names: list[str]) -> dict[str, list[str]]:
    facts: dict[str, list[str]] = {}
    for name in hero_names:
        if not name:
            continue
        rows = FACTS.get(str(name))
        if rows:
            facts[str(name)] = rows
    return facts
