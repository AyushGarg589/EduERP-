document.addEventListener("DOMContentLoaded", function () {

    const countrySelect = document.getElementById("country");
    const stateSelect = document.getElementById("state");
    const citySelect = document.getElementById("city");
    const hasCitySelect = citySelect && citySelect.tagName === "SELECT";
    const initialCountry = (countrySelect && countrySelect.dataset.currentCountry || "").trim();
    const initialState = (stateSelect && stateSelect.dataset.currentState || "").trim();
    const initialCity = (hasCitySelect && citySelect.dataset.currentCity || "").trim();

    /*
     * Stop if country/state fields are not present.
     */
    if (!countrySelect || !stateSelect) {
        return;
    }


    /*
     * State Tom Select instance.
     *
     * It will be created only after
     * states are received from the API.
     */

    let stateTomSelect = null;
    let cityTomSelect = null;
    let stateRequestId = 0;
    let cityRequestId = 0;
    let countryTomSelect = null;

    function clearCities(message) {
        cityRequestId += 1;

        if (!hasCitySelect) {
            return;
        }

        if (cityTomSelect) {
            cityTomSelect.destroy();
            cityTomSelect = null;
        }

        citySelect.innerHTML = "";

        const option = document.createElement("option");
        option.value = "";
        option.textContent = message;
        citySelect.appendChild(option);
        citySelect.disabled = true;
    }


    function initializeCitySelect(placeholder) {
        citySelect.disabled = false;
        cityTomSelect = new TomSelect(
            "#city",
            {
                placeholder: placeholder,
                searchField: ["text"],
                create: true,
                maxOptions: null
            }
        );
    }


    /*
     * -----------------------------------------
     * Load States
     * -----------------------------------------
     */

    async function loadStates(country) {
        const requestId = ++stateRequestId;
        clearCities("Select State First");

        /*
         * Destroy previous state Tom Select
         * before loading new states.
         */

        if (stateTomSelect) {

            stateTomSelect.destroy();

            stateTomSelect = null;
        }


        /*
         * Reset state dropdown.
         */

        stateSelect.innerHTML = `
            <option value="">
                Loading states...
            </option>
        `;

        stateSelect.disabled = true;


        /*
         * No country selected.
         */

        if (!country) {

            stateSelect.innerHTML = `
                <option value="">
                    Select Country First
                </option>
            `;

            return;
        }


        try {

            /*
             * Ask Django for states.
             */

            const response = await fetch(
                `/api/faculty/states/?country=${encodeURIComponent(country)}`
            );


            const data = await response.json();


            /*
             * Handle API error.
             */

            if (!response.ok || data.error) {

                throw new Error(
                    data.msg || data.error || "Unable to fetch states."
                );

            }

            if (requestId !== stateRequestId) {
                return;
            }

            /*
             * Reset dropdown.
             */

            stateSelect.innerHTML = `
                <option value="">
                    Select State
                </option>
            `;


            /*
             * Add states returned by API.
             */

            const states = data.data && Array.isArray(data.data.states)
                ? data.data.states
                    .map(function (state) {
                        return state && typeof state.name === "string"
                            ? state.name.trim()
                            : "";
                    })
                    .filter(Boolean)
                : [];

            states.forEach(function (stateName) {

                const option = document.createElement("option");
                option.value = stateName;
                option.textContent = stateName;
                stateSelect.appendChild(option);

            });


            /*
             * Enable state dropdown.
             */

            stateSelect.disabled = false;


            /*
             * Make state searchable.
             */

            stateTomSelect = new TomSelect(
                "#state",
                {
                    placeholder: "Search or select state...",
                    searchField: ["text"],
                    create: false,
                    maxOptions: null
                }
            );

            stateTomSelect.on("change", function (state) {
                loadCities(country, state);
            });

            if (
                country === initialCountry &&
                states.includes(initialState)
            ) {
                stateTomSelect.setValue(initialState, true);
                loadCities(country, initialState);
            }

            if (!states.length) {
                stateSelect.innerHTML = '<option value="">No states found</option>';
                stateTomSelect.destroy();
                stateTomSelect = null;
                stateSelect.disabled = true;
            }

        } catch (error) {

            if (requestId !== stateRequestId) {
                return;
            }

            console.error(
                "State API Error:",
                error
            );


            /*
             * Show error to user.
             */

            stateSelect.innerHTML = `
                <option value="">
                    Unable to load states
                </option>
            `;

            stateSelect.disabled = true;

        }

    }


    async function loadCities(country, state) {
        if (!hasCitySelect) {
            return;
        }

        const requestId = ++cityRequestId;

        if (cityTomSelect) {
            cityTomSelect.destroy();
            cityTomSelect = null;
        }

        citySelect.innerHTML = "";

        if (!country || !state) {
            const option = document.createElement("option");
            option.value = "";
            option.textContent = "Select State First";
            citySelect.appendChild(option);
            citySelect.disabled = true;
            return;
        }

        const loadingOption = document.createElement("option");
        loadingOption.value = "";
        loadingOption.textContent = "Loading cities...";
        citySelect.appendChild(loadingOption);
        citySelect.disabled = true;

        try {
            const params = new URLSearchParams({ country, state });
            const response = await fetch(
                `/api/faculty/cities/?${params.toString()}`
            );
            const data = await response.json();

            if (!response.ok || data.error) {
                throw new Error(
                    data.msg || data.error || "Unable to fetch cities."
                );
            }

            if (requestId !== cityRequestId) {
                return;
            }

            const cities = Array.isArray(data.data)
                ? [...new Set(data.data
                    .filter(function (city) {
                        return typeof city === "string" && city.trim();
                    })
                    .map(function (city) {
                        return city.trim();
                    }))]
                : [];

            citySelect.innerHTML = "";

            const placeholder = document.createElement("option");
            placeholder.value = "";
            placeholder.textContent = cities.length
                ? "Select City"
                : "No cities found - type to add";
            citySelect.appendChild(placeholder);

            cities.forEach(function (city) {
                const option = document.createElement("option");
                option.value = city;
                option.textContent = city;
                citySelect.appendChild(option);
            });

            const preserveCurrentCity =
                country === initialCountry &&
                state === initialState &&
                initialCity;
            if (preserveCurrentCity && !cities.includes(initialCity)) {
                const option = document.createElement("option");
                option.value = initialCity;
                option.textContent = initialCity;
                citySelect.appendChild(option);
            }

            initializeCitySelect("Search or enter city...");
            if (preserveCurrentCity) {
                cityTomSelect.setValue(initialCity, true);
            }
        } catch (error) {
            if (requestId !== cityRequestId) {
                return;
            }

            console.error("City API Error:", error);
            citySelect.innerHTML = "";

            const placeholder = document.createElement("option");
            placeholder.value = "";
            placeholder.textContent = "Cities unavailable - type to add";
            citySelect.appendChild(placeholder);

            initializeCitySelect("Enter city name...");
            if (
                country === initialCountry &&
                state === initialState &&
                initialCity
            ) {
                cityTomSelect.addOption({
                    value: initialCity,
                    text: initialCity
                });
                cityTomSelect.setValue(initialCity, true);
            }
        }
    }


    async function loadCountries() {
        countrySelect.innerHTML = '<option value="">Loading countries...</option>';
        countrySelect.disabled = true;

        try {
            const response = await fetch("/api/faculty/countries/");
            const data = await response.json();

            if (!response.ok || !Array.isArray(data.data)) {
                throw new Error(data.error || "Unable to fetch countries.");
            }

            const countries = [...new Set(data.data
                .filter(function (country) {
                    return typeof country === "string" && country.trim();
                })
                .map(function (country) {
                    return country.trim();
                }))].sort(function (first, second) {
                return first.localeCompare(second);
            });

            if (!countries.length) {
                throw new Error("The country provider returned no countries.");
            }

            countrySelect.innerHTML = '<option value="">Select Country</option>';
            const preferredCountry = countries.includes(initialCountry)
                ? initialCountry
                : "India";
            countries.forEach(function (country) {
                const option = document.createElement("option");
                option.value = country;
                option.textContent = country;
                option.selected = country === preferredCountry;
                countrySelect.appendChild(option);
            });
            countrySelect.disabled = false;

            countryTomSelect = new TomSelect(countrySelect, {
                placeholder: "Search or select country...",
                searchField: ["text"],
                create: false,
                maxOptions: null,
                sortField: {
                    field: "text",
                    direction: "asc"
                }
            });

            countryTomSelect.on("change", loadStates);
            loadStates(countryTomSelect.getValue());
        } catch (error) {
            console.error("Country API Error:", error);
            countrySelect.innerHTML = '<option value="">Unable to load countries</option>';
            countrySelect.disabled = true;
            stateSelect.innerHTML = '<option value="">Select Country First</option>';
            stateSelect.disabled = true;
            clearCities("Select State First");
        }
    }


    /*
     * -----------------------------------------
     * Load countries, then default country states
     * -----------------------------------------
     */
    loadCountries();

});