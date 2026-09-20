/* ============================================================
   SIXTH SENSE
   Clean hackathon demo script.js

   Images expected:
   /website/images/StandardChicken.png
   /website/images/MildChicken.png
   /website/images/StressedChicken.png

   Live mode:
   Python /api/current controls the state.

   Demo mode:
   The demo buttons temporarily override the visual state.
   ============================================================ */


/* =========================
   CONFIGURATION
   ========================= */

const STORE = {
    theme: "sixth-sense-theme",
    mute: "sixth-sense-mute"
};

const STATE_LABEL = {
    stable: "Stable",
    elevated: "Elevated",
    highDistress: "High Distress Signal"
};

const STATE_COPY = {
    stable:
        "Signals are close to the participant's physiological baseline.",

    elevated:
        "A meaningful physiological change from baseline has been detected. Consider checking in with the participant.",

    highDistress:
        "A stronger physiological change from baseline has been detected. Consider checking in and reviewing the surrounding context."
};

const STATE_ICONS = {
    stable: "/website/images/StandardChicken.png",
    elevated: "/website/images/MildChicken.png",
    highDistress: "/website/images/StressedChicken.png"
};

const ZONE_LABEL = {
    head: "Head",
    chest: "Chest",
    abdomen: "Abdomen",
    "arm-l": "Left arm",
    "arm-r": "Right arm",
    "leg-l": "Left leg",
    "leg-r": "Right leg"
};


/* =========================
   GLOBAL STATE
   ========================= */

let demoStateOverride = null;
let latestReading = null;

const chart = {
    raw: []
};


/* =========================
   PRELOAD CHICKEN IMAGES
   ========================= */

Object.values(STATE_ICONS).forEach((src) => {

    const image = new Image();

    image.src = src;
});


/* =========================
   HELPER FUNCTIONS
   ========================= */

function pythonStateToKey(state) {

    const value = String(state || "")
        .trim()
        .toLowerCase();

    if (value === "elevated") {
        return "elevated";
    }

    if (
        value === "high distress signal" ||
        value === "highdistress" ||
        value === "high_distress"
    ) {
        return "highDistress";
    }

    return "stable";
}


function escapeHTML(value) {

    const div = document.createElement("div");

    div.textContent =
        value == null
            ? ""
            : String(value);

    return div.innerHTML;
}


function isMuted() {

    try {

        return JSON.parse(
            localStorage.getItem(STORE.mute) ||
            "false"
        );

    } catch {

        return false;
    }
}


/* ============================================================
   THEME + MUTE
   ============================================================ */

function initGlobalControls() {

    const savedTheme =
        localStorage.getItem(STORE.theme) ||
        (
            window.matchMedia &&
            window.matchMedia(
                "(prefers-color-scheme: dark)"
            ).matches
                ? "dark"
                : "light"
        );


    document.documentElement.setAttribute(
        "data-theme",
        savedTheme
    );


    /* Theme buttons */

    document
        .querySelectorAll(
            '[data-action="toggle-theme"]'
        )
        .forEach((button) => {

            button.setAttribute(
                "aria-pressed",
                savedTheme === "dark"
                    ? "true"
                    : "false"
            );


            button.addEventListener(
                "click",
                () => {

                    const current =
                        document.documentElement
                            .getAttribute(
                                "data-theme"
                            );

                    const next =
                        current === "dark"
                            ? "light"
                            : "dark";


                    document.documentElement
                        .setAttribute(
                            "data-theme",
                            next
                        );


                    localStorage.setItem(
                        STORE.theme,
                        next
                    );


                    document
                        .querySelectorAll(
                            '[data-action="toggle-theme"]'
                        )
                        .forEach((btn) => {

                            btn.setAttribute(
                                "aria-pressed",
                                next === "dark"
                                    ? "true"
                                    : "false"
                            );
                        });
                }
            );
        });


    /* Mute buttons */

    syncMuteButtons(
        isMuted()
    );


    document
        .querySelectorAll(
            '[data-action="toggle-mute"]'
        )
        .forEach((button) => {

            button.addEventListener(
                "click",
                () => {

                    const next =
                        !isMuted();


                    localStorage.setItem(
                        STORE.mute,
                        JSON.stringify(next)
                    );


                    syncMuteButtons(next);
                }
            );
        });
}


function syncMuteButtons(muted) {

    document
        .querySelectorAll(
            '[data-action="toggle-mute"]'
        )
        .forEach((button) => {

            button.setAttribute(
                "aria-pressed",
                muted
                    ? "true"
                    : "false"
            );


            button.title =
                muted
                    ? "Unmute alerts"
                    : "Mute all alerts";
        });
}


/* ============================================================
   STATE DISPLAY
   ============================================================ */

function applyState(
    stateKey,
    isDemo = false
) {

    if (!STATE_LABEL[stateKey]) {
        stateKey = "stable";
    }


    const hearth =
        document.getElementById(
            "hearth"
        );


    if (!hearth) {
        return;
    }


    hearth.dataset.state =
        stateKey;


    /* STATE NAME */

    const stateLabel =
        document.getElementById(
            "stateLabel"
        );


    if (stateLabel) {

        stateLabel.textContent =
            STATE_LABEL[stateKey] +
            (
                isDemo
                    ? " · DEMO"
                    : ""
            );
    }


    /* DESCRIPTION */

    const stateCopy =
        document.getElementById(
            "stateCopy"
        );


    if (stateCopy) {

        stateCopy.textContent =
            STATE_COPY[stateKey];
    }


    /* CHICKEN IMAGE */

    const stateEmoji =
        document.getElementById(
            "stateEmoji"
        );


    if (
        stateEmoji &&
        STATE_ICONS[stateKey]
    ) {

        const newImage =
            STATE_ICONS[stateKey];


        if (
            stateEmoji.getAttribute("src") !==
            newImage
        ) {

            stateEmoji.style.opacity =
                "0.3";


            setTimeout(
                () => {

                    stateEmoji.src =
                        newImage;


                    stateEmoji.alt =
                        STATE_LABEL[stateKey] +
                        " physiological state";


                    stateEmoji.style.opacity =
                        "1";

                },
                120
            );
        }
    }


    /* UPDATED TIME */

    const updatedAt =
        document.getElementById(
            "updatedAt"
        );


    if (updatedAt) {

        if (isDemo) {

            updatedAt.textContent =
                "Demo state";

        } else {

            updatedAt.textContent =
                "Updated " +
                new Date()
                    .toLocaleTimeString();
        }
    }


    /* THREE STATE PIPS */

    const level = {
        stable: 1,
        elevated: 2,
        highDistress: 3
    }[stateKey];


    document
        .querySelectorAll(
            ".scale-pip"
        )
        .forEach(
            (pip, index) => {

                pip.classList.toggle(
                    "filled",
                    index < level
                );
            }
        );
}


/* ============================================================
   DEMO BUTTONS
   ============================================================ */

function initDemoControls() {

    const buttons =
        document.querySelectorAll(
            "[data-demo-state]"
        );


    if (!buttons.length) {
        return;
    }


    buttons.forEach(
        (button) => {

            button.addEventListener(
                "click",
                () => {

                    const requested =
                        button.dataset.demoState;


                    /* Remove old active state */

                    buttons.forEach(
                        (btn) => {

                            btn.classList.remove(
                                "active"
                            );
                        }
                    );


                    button.classList.add(
                        "active"
                    );


                    /* LIVE EEG */

                    if (
                        requested === "live"
                    ) {

                        demoStateOverride =
                            null;


                        if (latestReading) {

                            applyState(
                                pythonStateToKey(
                                    latestReading.state
                                ),
                                false
                            );
                        }

                        return;
                    }


                    /* DEMO OVERRIDE */

                    demoStateOverride =
                        requested;


                    applyState(
                        demoStateOverride,
                        true
                    );
                }
            );
        }
    );
}


/* ============================================================
   ROOM SENSORS
   ============================================================ */

function updateSensors(data) {

    const sensors =
        data.sensors ||
        data.sensor_data ||
        data.environment ||
        data;


    const temperature =
        sensors.temperature ??
        sensors.temp;


    const humidity =
        sensors.humidity;


    const noise =
        sensors.noise ??
        sensors.noise_level;


    const temperatureInput =
        document.getElementById(
            "sensorTemp"
        );


    const humidityInput =
        document.getElementById(
            "sensorHumidity"
        );


    const noiseInput =
        document.getElementById(
            "sensorNoise"
        );


    if (
        temperatureInput &&
        temperature != null
    ) {

        temperatureInput.value =
            Number(
                temperature
            ).toFixed(1);
    }


    if (
        humidityInput &&
        humidity != null
    ) {

        humidityInput.value =
            Math.round(
                Number(humidity)
            );
    }


    if (
        noiseInput &&
        noise != null
    ) {

        noiseInput.value =
            Number(
                noise
            ).toFixed(1);
    }


    const reading =
        document.getElementById(
            "sensorReading"
        );


    if (reading) {

        const parts = [];


        if (temperature != null) {

            parts.push(
                Number(
                    temperature
                ).toFixed(1) +
                " °C"
            );
        }


        if (humidity != null) {

            parts.push(
                Math.round(
                    Number(humidity)
                ) +
                "% humidity"
            );
        }


        if (noise != null) {

            parts.push(
                Number(
                    noise
                ).toFixed(1) +
                " dB"
            );
        }


        reading.textContent =
            parts.length
                ? "Latest context: " +
                  parts.join(" · ")
                : "Waiting for room sensor data…";
    }
}


/* ============================================================
   EEG / SIGNAL GRAPH
   ============================================================ */

function createChartPoints(
    values
) {

    if (!values.length) {
        return "";
    }


    let minimum =
        Math.min(...values);


    let maximum =
        Math.max(...values);


    if (
        maximum === minimum
    ) {

        minimum -= 1;
        maximum += 1;
    }


    return values
        .map(
            (value, index) => {

                const x =
                    index *
                    600 /
                    Math.max(
                        1,
                        values.length - 1
                    );


                const normalized =
                    (
                        value -
                        minimum
                    ) /
                    (
                        maximum -
                        minimum
                    );


                const y =
                    154 -
                    normalized *
                    148;


                return (
                    x.toFixed(1) +
                    "," +
                    y.toFixed(1)
                );
            }
        )
        .join(" ");
}


function calculateSmoothedSeries(
    values
) {

    return values.map(
        (_, index) => {

            const start =
                Math.max(
                    0,
                    index - 7
                );


            const section =
                values.slice(
                    start,
                    index + 1
                );


            return (
                section.reduce(
                    (sum, value) =>
                        sum + value,
                    0
                ) /
                section.length
            );
        }
    );
}


function updateChart(data) {

    let incoming =
        data.eeg_trace;


    /* Sometimes EEG can arrive nested */

    if (
        Array.isArray(incoming) &&
        Array.isArray(incoming[0])
    ) {

        incoming =
            incoming[0];
    }


    /* Actual EEG trace */

    if (
        Array.isArray(incoming) &&
        incoming.length
    ) {

        const step =
            Math.max(
                1,
                Math.floor(
                    incoming.length /
                    20
                )
            );


        for (
            let index = 0;
            index < incoming.length;
            index += step
        ) {

            const value =
                Number(
                    incoming[index]
                );


            if (
                Number.isFinite(value)
            ) {

                chart.raw.push(
                    value
                );
            }
        }

    } else {

        /* Fallback for simulation */

        const value =
            Number(
                data.arousal ??
                data.features?.arousal
            );


        if (
            Number.isFinite(value)
        ) {

            chart.raw.push(
                value
            );
        }
    }


    /* Keep graph manageable */

    chart.raw =
        chart.raw.slice(
            -120
        );


    const smooth =
        calculateSmoothedSeries(
            chart.raw
        );


    const rawPoints =
        createChartPoints(
            chart.raw
        );


    const smoothPoints =
        createChartPoints(
            smooth
        );


    const rawLine =
        document.getElementById(
            "rawLine"
        );


    const smoothLine =
        document.getElementById(
            "smoothLine"
        );


    const smoothFill =
        document.getElementById(
            "smoothFill"
        );


    if (rawLine) {

        rawLine.setAttribute(
            "points",
            rawPoints
        );
    }


    if (smoothLine) {

        smoothLine.setAttribute(
            "points",
            smoothPoints
        );
    }


    if (smoothFill) {

        smoothFill.setAttribute(
            "points",
            smoothPoints
                ? (
                    "0,160 " +
                    smoothPoints +
                    " 600,160"
                )
                : ""
        );
    }
}


/* ============================================================
   FASTAPI LIVE POLLING
   ============================================================ */

async function pollCurrentReading() {

    try {

        const response =
            await fetch(
                "/api/current",
                {
                    cache: "no-store"
                }
            );


        if (!response.ok) {

            throw new Error(
                "API error " +
                response.status
            );
        }


        const data =
            await response.json();


        latestReading =
            data;


        /* IMPORTANT:
           Demo state wins while a demo
           button is selected.
        */

        if (
            demoStateOverride !== null
        ) {

            applyState(
                demoStateOverride,
                true
            );

        } else {

            applyState(
                pythonStateToKey(
                    data.state
                ),
                false
            );
        }


        updateSensors(data);

        updateChart(data);


    } catch (error) {

        console.error(
            "Could not get /api/current:",
            error
        );


        const updatedAt =
            document.getElementById(
                "updatedAt"
            );


        if (updatedAt) {

            updatedAt.textContent =
                "Backend unavailable";
        }
    }
}


function initDashboard() {

    const hearth =
        document.getElementById(
            "hearth"
        );


    if (!hearth) {
        return;
    }


    applyState(
        "stable",
        false
    );


    pollCurrentReading();


    setInterval(
        pollCurrentReading,
        1000
    );
}


/* ============================================================
   PAIN VISUALIZER
   ============================================================ */

function initPainMap() {

    const diagram =
        document.getElementById(
            "bodyDiagram"
        );


    if (!diagram) {
        return;
    }


    const zones =
        Array.from(
            diagram.querySelectorAll(
                ".zone"
            )
        );


    const painList =
        document.getElementById(
            "painList"
        );


    const painDetails =
        document.getElementById(
            "painDetails"
        );


    const painLevel =
        document.getElementById(
            "painLevel"
        );


    const painLevelValue =
        document.getElementById(
            "painLevelValue"
        );


    function renderPainZones() {

        if (!painList) {
            return;
        }


        const selected =
            zones.filter(
                (zone) =>
                    Number(
                        zone.dataset.intensity
                    ) > 0
            );


        if (!selected.length) {

            painList.innerHTML =
                `
                <div class="pain-row">
                    <span class="none">
                        No regions selected
                    </span>
                </div>
                `;

            return;
        }


        painList.innerHTML =
            selected
                .map(
                    (zone) => {

                        const intensity =
                            Number(
                                zone.dataset.intensity
                            );


                        return `
                            <div class="pain-row">
                                <span>
                                    ${
                                        escapeHTML(
                                            ZONE_LABEL[
                                                zone.dataset.zone
                                            ] ||
                                            zone.dataset.zone
                                        )
                                    }
                                </span>

                                <strong>
                                    ${intensity}/3
                                </strong>
                            </div>
                        `;
                    }
                )
                .join("");
    }


    zones.forEach(
        (zone) => {

            zone.addEventListener(
                "click",
                () => {

                    const current =
                        Number(
                            zone.dataset.intensity ||
                            0
                        );


                    const next =
                        (
                            current + 1
                        ) % 4;


                    zone.dataset.intensity =
                        String(next);


                    renderPainZones();
                }
            );
        }
    );


    document
        .querySelectorAll(
            'input[name="painPresent"]'
        )
        .forEach(
            (radio) => {

                radio.addEventListener(
                    "change",
                    () => {

                        const selected =
                            document.querySelector(
                                'input[name="painPresent"]:checked'
                            );


                        if (painDetails) {

                            painDetails.hidden =
                                !selected ||
                                selected.value ===
                                    "No";
                        }
                    }
                );
            }
        );


    if (painLevel) {

        painLevel.addEventListener(
            "input",
            () => {

                if (painLevelValue) {

                    painLevelValue.textContent =
                        painLevel.value;
                }
            }
        );
    }


    const saveButton =
        document.getElementById(
            "savePainObservation"
        );


    if (saveButton) {

        saveButton.addEventListener(
            "click",
            async () => {

                const selectedPain =
                    document.querySelector(
                        'input[name="painPresent"]:checked'
                    );


                const locations =
                    zones
                        .filter(
                            (zone) =>
                                Number(
                                    zone.dataset.intensity
                                ) > 0
                        )
                        .map(
                            (zone) =>
                                ZONE_LABEL[
                                    zone.dataset.zone
                                ] ||
                                zone.dataset.zone
                        );


                const painTypes =
                    Array.from(
                        document.querySelectorAll(
                            'input[name="painType"]:checked'
                        )
                    )
                    .map(
                        (input) =>
                            input.value
                    );


                const payload = {

                    participant_id:
                        "P01",

                    pain_present:
                        selectedPain
                            ? selectedPain.value
                            : "No",

                    pain_location:
                        locations,

                    pain_level:
                        Number(
                            painLevel
                                ? painLevel.value
                                : 0
                        ),

                    pain_type:
                        painTypes,

                    pain_note:
                        document
                            .getElementById(
                                "painNote"
                            )
                            ?.value ||
                        "",

                    note:
                        document
                            .getElementById(
                                "caregiverNote"
                            )
                            ?.value ||
                        ""
                };


                const status =
                    document.getElementById(
                        "painSaveStatus"
                    );


                try {

                    saveButton.disabled =
                        true;


                    if (status) {

                        status.textContent =
                            "Saving…";
                    }


                    const response =
                        await fetch(
                            "/api/event",
                            {
                                method:
                                    "POST",

                                headers: {
                                    "Content-Type":
                                        "application/json"
                                },

                                body:
                                    JSON.stringify(
                                        payload
                                    )
                            }
                        );


                    if (!response.ok) {

                        throw new Error(
                            "API error " +
                            response.status
                        );
                    }


                    if (status) {

                        status.textContent =
                            "Observation saved.";
                    }


                } catch (error) {

                    console.error(
                        "Could not save observation:",
                        error
                    );


                    if (status) {

                        status.textContent =
                            "Could not save. Check backend.";
                    }


                } finally {

                    saveButton.disabled =
                        false;
                }
            }
        );
    }


    renderPainZones();
}


/* ============================================================
   HISTORY API
   ============================================================ */

async function getHistory() {

    const response =
        await fetch(
            "/api/history",
            {
                cache:
                    "no-store"
            }
        );


    if (!response.ok) {

        throw new Error(
            "History API error"
        );
    }


    const data =
        await response.json();


    if (
        Array.isArray(data)
    ) {

        return data;
    }


    return (
        data.history ||
        data.events ||
        data.records ||
        []
    );
}


/* ============================================================
   SAVED EVENTS PAGE
   ============================================================ */

function initEventsPage() {

    const eventsList =
        document.getElementById(
            "eventsList"
        );


    if (!eventsList) {
        return;
    }


    let events = [];

    let currentFilter =
        "all";


    function renderEvents() {

        const filtered =
            events
                .slice()
                .reverse()
                .filter(
                    (event) => {

                        if (
                            currentFilter ===
                            "all"
                        ) {

                            return true;
                        }


                        return (
                            pythonStateToKey(
                                event.state ||
                                event.to_state
                            ) ===
                            currentFilter
                        );
                    }
                );


        if (!filtered.length) {

            eventsList.innerHTML =
                `
                <div class="empty-state">
                    <h3>No matching events yet</h3>
                    <p>
                        State shifts and caregiver
                        observations will appear here.
                    </p>
                </div>
                `;

            return;
        }


        eventsList.innerHTML =
            filtered
                .map(
                    (event) => {

                        const key =
                            pythonStateToKey(
                                event.state ||
                                event.to_state
                            );


                        const timestamp =
                            event.timestamp
                                ? new Date(
                                    event.timestamp
                                )
                                    .toLocaleString()
                                : "Recorded event";


                        const note =
                            event.note ||
                            event.pain_note ||
                            "";


                        return `
                            <article class="event-card">

                                <div class="event-head">

                                    <span
                                        class="state-chip ${key}"
                                    >
                                        ${
                                            STATE_LABEL[
                                                key
                                            ]
                                        }
                                    </span>

                                    <span
                                        class="event-time"
                                    >
                                        ${
                                            escapeHTML(
                                                timestamp
                                            )
                                        }
                                    </span>

                                </div>

                                ${
                                    note
                                        ? `
                                            <div>
                                                ${
                                                    escapeHTML(
                                                        note
                                                    )
                                                }
                                            </div>
                                          `
                                        : ""
                                }

                            </article>
                        `;
                    }
                )
                .join("");
    }


    document
        .querySelectorAll(
            "#eventFilters [data-filter]"
        )
        .forEach(
            (button) => {

                button.addEventListener(
                    "click",
                    () => {

                        document
                            .querySelectorAll(
                                "#eventFilters [data-filter]"
                            )
                            .forEach(
                                (btn) =>
                                    btn.classList.remove(
                                        "active"
                                    )
                            );


                        button.classList.add(
                            "active"
                        );


                        currentFilter =
                            button.dataset.filter;


                        renderEvents();
                    }
                );
            }
        );


    getHistory()
        .then(
            (history) => {

                events =
                    history;

                renderEvents();
            }
        )
        .catch(
            (error) => {

                console.error(
                    error
                );


                eventsList.innerHTML =
                    `
                    <div class="empty-state">
                        <h3>
                            Could not load history
                        </h3>

                        <p>
                            Make sure the FastAPI
                            server is running.
                        </p>
                    </div>
                    `;
            }
        );
}


/* ============================================================
   DOCTOR SUMMARY
   ============================================================ */

async function initDoctorSummary() {

    const root =
        document.getElementById(
            "summaryRoot"
        );


    if (!root) {
        return;
    }


    const printButton =
        document.getElementById(
            "printSummary"
        );


    if (printButton) {

        printButton.addEventListener(
            "click",
            () => {

                window.print();
            }
        );
    }


    let history = [];

    let current =
        null;


    try {

        history =
            await getHistory();

    } catch (error) {

        console.warn(
            "History unavailable:",
            error
        );
    }


    try {

        const response =
            await fetch(
                "/api/current",
                {
                    cache:
                        "no-store"
                }
            );


        if (response.ok) {

            current =
                await response.json();
        }

    } catch (error) {

        console.warn(
            "Current reading unavailable:",
            error
        );
    }


    /* CURRENT STATE */

    const currentState =
        document.getElementById(
            "sumCurrentState"
        );


    if (currentState) {

        if (current) {

            const key =
                pythonStateToKey(
                    current.state
                );


            currentState.textContent =
                STATE_LABEL[key];

        } else {

            currentState.textContent =
                "—";
        }
    }


    /* TOTAL SHIFTS */

    const totalShifts =
        document.getElementById(
            "sumTotalShifts"
        );


    if (totalShifts) {

        totalShifts.textContent =
            history.length;
    }


    /* HIGH DISTRESS COUNT */

    const highDistressCount =
        history.filter(
            (event) => {

                return (
                    pythonStateToKey(
                        event.state ||
                        event.to_state
                    ) ===
                    "highDistress"
                );
            }
        ).length;


    const distressElement =
        document.getElementById(
            "sumExtremeCount"
        );


    if (distressElement) {

        distressElement.textContent =
            highDistressCount;
    }


    /* DISTRIBUTION */

    const counts = {
        stable: 0,
        elevated: 0,
        highDistress: 0
    };


    history.forEach(
        (event) => {

            const key =
                pythonStateToKey(
                    event.state ||
                    event.to_state
                );


            counts[key] += 1;
        }
    );


    const total =
        history.length || 1;


    Object
        .keys(counts)
        .forEach(
            (key) => {

                const percentage =
                    Math.round(
                        counts[key] *
                        100 /
                        total
                    );


                const segment =
                    document.querySelector(
                        ".dist-bar .seg." +
                        key
                    );


                if (segment) {

                    segment.style.width =
                        percentage +
                        "%";
                }


                const label =
                    document.getElementById(
                        "distLabel-" +
                        key
                    );


                if (label) {

                    label.textContent =
                        percentage +
                        "%";
                }
            }
        );


    /* EVENT TABLE */

    const eventBody =
        document.getElementById(
            "eventSummaryBody"
        );


    if (eventBody) {

        const rows =
            history
                .slice(-10)
                .reverse();


        if (!rows.length) {

            eventBody.innerHTML =
                `
                <tr>
                    <td colspan="3">
                        No events recorded yet.
                    </td>
                </tr>
                `;

        } else {

            eventBody.innerHTML =
                rows
                    .map(
                        (event) => {

                            const key =
                                pythonStateToKey(
                                    event.state ||
                                    event.to_state
                                );


                            const timestamp =
                                event.timestamp
                                    ? new Date(
                                        event.timestamp
                                    )
                                        .toLocaleString()
                                    : "—";


                            return `
                                <tr>

                                    <td>
                                        ${
                                            escapeHTML(
                                                timestamp
                                            )
                                        }
                                    </td>

                                    <td>
                                        ${
                                            escapeHTML(
                                                STATE_LABEL[
                                                    key
                                                ]
                                            )
                                        }
                                    </td>

                                    <td>
                                        ${
                                            escapeHTML(
                                                event.note ||
                                                event.pain_note ||
                                                ""
                                            )
                                        }
                                    </td>

                                </tr>
                            `;
                        }
                    )
                    .join("");
        }
    }
}


/* ============================================================
   START SIXTH SENSE
   ============================================================ */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        initGlobalControls();

        initDashboard();

        initDemoControls();

        initPainMap();

        initEventsPage();

        initDoctorSummary();
    }
);