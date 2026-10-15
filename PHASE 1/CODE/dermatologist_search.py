import streamlit as st
import requests
from streamlit_geolocation import streamlit_geolocation
from geopy.distance import geodesic
from urllib.parse import quote


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Nearby Dermatologists",
    page_icon="🩺",
    layout="wide"
)


# ============================================================
# PAGE TITLE
# ============================================================

st.title("🩺 Nearby Dermatologists")

st.write(
    "Find dermatologists and skin clinics within 20 km "
    "of your current location."
)


# ============================================================
# GET USER LOCATION
# ============================================================

location = streamlit_geolocation()


if not location or location.get("latitude") is None:

    st.info(
        "📍 Please allow location access to find "
        "nearby dermatologists."
    )

    st.stop()


latitude = float(location["latitude"])
longitude = float(location["longitude"])


st.success("📍 Your location was detected successfully!")


# ============================================================
# SEARCH USING PHOTON
# ============================================================

def search_photon(search_text, lat, lon):

    url = "https://photon.komoot.io/api/"

    params = {
        "q": search_text,
        "lat": lat,
        "lon": lon,
        "limit": 20
    }

    headers = {
        "User-Agent": "DermaAI-Educational-Project/1.0"
    }

    try:

        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        return data.get("features", [])

    except requests.exceptions.RequestException as error:

        st.error(
            f"Unable to search nearby places: {error}"
        )

        return []


# ============================================================
# SEARCH TERMS
# ============================================================

search_terms = [
    "dermatologist",
    "dermatology clinic",
    "skin clinic",
    "skin hospital",
    "derma clinic"
]


# ============================================================
# SEARCH NEAR USER
# ============================================================

all_results = []


with st.spinner(
    "🔎 Finding dermatologists within 20 km..."
):

    for search_term in search_terms:

        results = search_photon(
            search_term,
            latitude,
            longitude
        )

        all_results.extend(results)


# ============================================================
# PROCESS RESULTS
# ============================================================

clinics = []


for result in all_results:

    properties = result.get(
        "properties",
        {}
    )

    geometry = result.get(
        "geometry",
        {}
    )

    coordinates = geometry.get(
        "coordinates",
        []
    )


    if len(coordinates) < 2:
        continue


    # GeoJSON coordinates are:
    # longitude, latitude

    place_longitude = float(
        coordinates[0]
    )

    place_latitude = float(
        coordinates[1]
    )


    # --------------------------------------------------------
    # CALCULATE DISTANCE
    # --------------------------------------------------------

    try:

        distance = geodesic(
            (latitude, longitude),
            (place_latitude, place_longitude)
        ).km

    except Exception:

        continue


    # --------------------------------------------------------
    # ONLY KEEP PLACES WITHIN 20 KM
    # --------------------------------------------------------

    if distance > 20:
        continue


    # --------------------------------------------------------
    # GET CLINIC NAME
    # --------------------------------------------------------

    name = (
        properties.get("name")
        or properties.get("street")
        or "Dermatology Clinic"
    )


    # --------------------------------------------------------
    # BUILD ADDRESS
    # --------------------------------------------------------

    address_parts = []


    for key in [
        "housenumber",
        "street",
        "district",
        "city",
        "postcode"
    ]:

        value = properties.get(key)


        if value:

            value = str(value)


            if value not in address_parts:

                address_parts.append(value)


    address = ", ".join(
        address_parts
    )


    # --------------------------------------------------------
    # PHONE
    # --------------------------------------------------------

    phone = (
        properties.get("phone")
        or properties.get("contact:phone")
    )


    # --------------------------------------------------------
    # WEBSITE
    # --------------------------------------------------------

    website = (
        properties.get("website")
        or properties.get("contact:website")
    )


    clinics.append({

        "name": name,

        "distance": distance,

        "address": address,

        "phone": phone,

        "website": website,

        "latitude": place_latitude,

        "longitude": place_longitude

    })


# ============================================================
# REMOVE DUPLICATES
# ============================================================

unique_clinics = {}


for clinic in clinics:

    key = (

        clinic["name"]
        .strip()
        .lower(),

        round(
            clinic["latitude"],
            4
        ),

        round(
            clinic["longitude"],
            4
        )

    )


    unique_clinics[key] = clinic


clinics = list(
    unique_clinics.values()
)


# ============================================================
# SORT BY DISTANCE
# ============================================================

clinics.sort(
    key=lambda clinic:
    clinic["distance"]
)


# ============================================================
# DISPLAY RESULTS
# ============================================================

if not clinics:

    st.warning(
        "No dermatologist or skin clinic "
        "was found within 20 km."
    )

    st.info(
        "Your location was detected, but the "
        "free OpenStreetMap-based database may "
        "not contain clinics in this area."
    )


else:

    st.subheader(
        "🩺 Dermatologists Near You"
    )

    st.caption(
        "Results are sorted from nearest to farthest. "
        "Maximum distance: 20 km."
    )


    # Show maximum 10 results

    for index, clinic in enumerate(
        clinics[:10],
        start=1
    ):

        st.markdown("---")


        # ----------------------------------------------------
        # CLINIC NAME
        # ----------------------------------------------------

        st.markdown(
            f"### {index}. 🩺 {clinic['name']}"
        )


        # ----------------------------------------------------
        # DISTANCE
        # ----------------------------------------------------

        if clinic["distance"] < 1:

            distance_text = (
                f"{clinic['distance'] * 1000:.0f} meters"
            )

        else:

            distance_text = (
                f"{clinic['distance']:.2f} km"
            )


        st.write(
            f"📏 **{distance_text} away**"
        )


        # ----------------------------------------------------
        # ADDRESS
        # ----------------------------------------------------

        if clinic["address"]:

            st.write(
                f"📍 {clinic['address']}"
            )

        else:

            st.write(
                "📍 Address not available"
            )


        # ----------------------------------------------------
        # GOOGLE MAPS DIRECTIONS
        # ----------------------------------------------------

        maps_url = (
            "https://www.google.com/maps/dir/?api=1"
            f"&destination="
            f"{clinic['latitude']},"
            f"{clinic['longitude']}"
        )


        # ----------------------------------------------------
        # CONTACT SEARCH
        # ----------------------------------------------------

        search_text = quote(
            f"{clinic['name']} "
            f"{clinic['address']}"
        )


        contact_search_url = (
            "https://www.google.com/search?q="
            f"{search_text}"
        )


        # ----------------------------------------------------
        # WEBSITE / CLINIC INFO
        # ----------------------------------------------------

        if clinic["website"]:

            website_url = clinic["website"]

        else:

            website_url = contact_search_url


        # ----------------------------------------------------
        # BUTTONS
        # ----------------------------------------------------

        col1, col2, col3 = st.columns(3)


        # Directions

        with col1:

            st.link_button(
                "📍 Directions",
                maps_url
            )


        # Call / Contact

        with col2:

            if clinic["phone"]:

                phone_url = (
                    "tel:"
                    + str(clinic["phone"])
                )

                st.link_button(
                    "📞 Call",
                    phone_url
                )

            else:

                st.link_button(
                    "🔎 Contact",
                    contact_search_url
                )


        # Website / Clinic Info

        with col3:

            if clinic["website"]:

                st.link_button(
                    "🌐 Website",
                    website_url
                )

            else:

                st.link_button(
                    "🌐 Clinic Info",
                    contact_search_url
                )


# ============================================================
# INFORMATION
# ============================================================

st.markdown("---")

st.caption(
    "📍 Location-based results are calculated from "
    "the user's browser location."
)

st.caption(
    "🗺️ Place data: OpenStreetMap / Photon."
)