from config import sport_now_collection, logger


def save_sport_now(sport_info, user_name):
    """Save sport activity to database."""
    # Add user information
    sport_info['name'] = user_name
    if 'district' not in sport_info or not sport_info['district']:
        sport_info['district'] = "Unknown"

    # Store in database
    result = sport_now_collection.insert_one(sport_info)
    return result.inserted_id is not None


def find_sport_buddies(sport_query, district_query=""):
    """Find sport buddies based on sport and location."""
    # Find exact matches first
    exact_matches = list(sport_now_collection.find({"sport": {"$regex": f"^{sport_query}$", "$options": "i"}}))

    # If no exact matches, try partial matches
    if not exact_matches:
        partial_matches = list(sport_now_collection.find({"sport": {"$regex": sport_query, "$options": "i"}}))
        matches = partial_matches
    else:
        matches = exact_matches

    # Filter by district if provided
    if district_query and district_query.lower() != "unknown":
        district_matches = [m for m in matches if district_query.lower() in m.get('district', '').lower()]
        if district_matches:
            matches = district_matches

    # Limit to top 3 matches
    matches = matches[:3]

    # Count players by location
    location_counts = {}
    for match in matches:
        location = match.get('location', 'Unknown location')
        if location in location_counts:
            location_counts[location] += 1
        else:
            location_counts[location] = 1

    return matches, location_counts