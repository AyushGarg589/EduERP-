import unicodedata

import requests 

from django.http import JsonResponse

from django.views import View




class FacultyStatesApi(View):
    """
    Fetch states for the selected country
    from the CountriesNow API.
    """

    def get(self, request, *args, **kwargs):

        country = request.GET.get("country")

        # Country is required
        if not country:
            return JsonResponse(
                {
                    "error": "Country is required."
                },
                status=400
            )

        try:

            response = requests.get(
                "https://countriesnow.space/api/v0.1/countries/states/q",
                params={
                    "country": country
                },
                timeout=10
            )

            response.raise_for_status()

            data = response.json()

            return JsonResponse(data)

        except requests.RequestException:

            return JsonResponse(
                {
                    "error": "Unable to fetch states."
                },
                status=503
            )


class FacultyCitiesApi(View):
    def get(self, request, *args, **kwargs):
        country = request.GET.get("country")
        state = request.GET.get("state")

        if not country or not state:
            return JsonResponse(
                {
                    "error": "Country and state are required."
                },
                status=400
            )

        try:
            response = requests.get(
                "https://countriesnow.space/api/v0.1/countries/state/cities/q",
                params={
                    "country": country,
                    "state": state,
                },
                timeout=10
            )
            response.raise_for_status()

            payload = response.json()

            if not isinstance(payload, dict):
                return JsonResponse(
                    {
                        "error": "City provider returned invalid data."
                    },
                    status=502
                )

            if payload.get("error"):
                return JsonResponse(
                    {
                        "error": payload.get(
                            "msg",
                            "Unable to fetch cities."
                        )
                    },
                    status=502
                )

            cities = payload.get("data")
            if not isinstance(cities, list):
                return JsonResponse(
                    {
                        "error": "City provider returned invalid data."
                    },
                    status=502
                )

            clean_cities = []
            seen_cities = set()

            for city in cities:
                if not isinstance(city, str):
                    continue

                normalized_city = "".join(
                    character
                    for character in unicodedata.normalize("NFKD", city)
                    if not unicodedata.category(character).startswith("M")
                ).strip()
                deduplication_key = normalized_city.casefold()

                if normalized_city and deduplication_key not in seen_cities:
                    seen_cities.add(deduplication_key)
                    clean_cities.append(normalized_city)

            return JsonResponse(
                {
                    "error": False,
                    "msg": "Cities retrieved successfully.",
                    "data": clean_cities,
                }
            )
        except requests.RequestException:
            return JsonResponse(
                {
                    "error": "Unable to fetch cities."
                },
                status=503
            )