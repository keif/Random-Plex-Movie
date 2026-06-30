const sectionEl = document.getElementById("section");
const loadingEl = document.getElementById("loading-overlay");
const errorStateEl = document.getElementById("error-state");
const errorMsgEl = document.getElementById("error-message");

const filterState = { genre: "", year_min: null, year_max: null, rating_min: null };

function activeFilterCount() {
    return [filterState.genre, filterState.year_min, filterState.year_max, filterState.rating_min]
        .filter(v => v !== "" && v !== null).length;
}

function updateFilterButton() {
    const count = activeFilterCount();
    document.getElementById("btn_filters").textContent = count > 0 ? `FILTERS (${count})` : "FILTERS";
}

function buildMovieUrl() {
    const params = new URLSearchParams();
    if (filterState.genre) params.set("genre", filterState.genre);
    if (filterState.year_min !== null) params.set("year_min", filterState.year_min);
    if (filterState.year_max !== null) params.set("year_max", filterState.year_max);
    if (filterState.rating_min !== null) params.set("rating_min", filterState.rating_min);
    const qs = params.toString();
    return qs ? `/api/movie?${qs}` : "/api/movie";
}

async function loadFilters() {
    try {
        const res = await fetch("/api/filters");
        if (!res.ok) return;
        const data = await res.json();
        const select = document.getElementById("filter_genre");
        (data.genres || []).forEach(g => {
            const opt = document.createElement("option");
            opt.value = g;
            opt.textContent = g;
            select.appendChild(opt);
        });
        if (data.year_min) document.getElementById("filter_year_min").placeholder = data.year_min;
        if (data.year_max) document.getElementById("filter_year_max").placeholder = data.year_max;
    } catch { /* non-critical — filters still usable without placeholder hints */ }
}

async function loadMovie() {
    sectionEl.classList.add("hidden");
    errorStateEl.classList.add("hidden");
    loadingEl.classList.remove("hidden");

    try {
        const res = await fetch(buildMovieUrl());
        const movie = await res.json();
        if (!res.ok) {
            showError(movie.error || "Failed to load a movie.");
            return;
        }
        displayMovie(movie);
        sectionEl.classList.remove("hidden");
    } catch {
        showError("Could not reach the server. Is the app running?");
    } finally {
        loadingEl.classList.add("hidden");
    }
}

function displayMovie(movie) {
    document.getElementById("title").textContent = movie.title;
    document.getElementById("year_duration").textContent =
        `${movie.year}  |  ${movie.duration_hours}h ${movie.duration_minutes}m`;

    const genresEl = document.getElementById("genres");
    genresEl.textContent = "";
    (movie.genres || []).forEach(g => {
        const span = document.createElement("span");
        span.className = "genre-tag";
        span.textContent = g;
        genresEl.appendChild(span);
    });

    const ratingEl = document.getElementById("rating");
    ratingEl.textContent = movie.rating ? `★ ${movie.rating} / 10` : "";

    document.getElementById("summary").textContent = movie.summary || "";

    setCrewLine("directors", "Directed by", movie.directors);
    setCrewLine("writers", "Written by", movie.writers);
    setCrewLine("actors", "Cast", movie.actors);

    const posterEl = document.getElementById("poster_img");
    posterEl.src = movie.poster || "";
    posterEl.alt = movie.title;

    const bgEl = document.getElementById("img_background");
    bgEl.style.backgroundImage = movie.background ? `url(${movie.background})` : "none";
}

function setCrewLine(id, label, names) {
    const el = document.getElementById(id);
    el.textContent = "";
    if (!names || names.length === 0) return;
    const bold = document.createElement("span");
    bold.style.fontWeight = "700";
    bold.textContent = `${label}: `;
    el.appendChild(bold);
    el.appendChild(document.createTextNode(names.join(", ")));
}

function showError(msg) {
    errorMsgEl.textContent = msg;
    errorStateEl.classList.remove("hidden");
    loadingEl.classList.add("hidden");
    sectionEl.classList.add("hidden");
}

function closeClientPrompt() {
    document.getElementById("client_prompt").classList.add("hidden");
}

document.getElementById("btn_next").addEventListener("click", loadMovie);

document.getElementById("btn_watch").addEventListener("click", async () => {
    const listEl = document.getElementById("list_of_clients");
    listEl.textContent = "";

    try {
        const res = await fetch("/api/clients");
        const data = await res.json();
        const clients = data.clients || [];

        if (clients.length === 0) {
            const msg = document.createElement("p");
            msg.className = "no-clients-msg";
            msg.textContent = "No Plex clients are currently online.";
            listEl.appendChild(msg);
        } else {
            clients.forEach(name => {
                const div = document.createElement("div");
                div.className = "client";
                const p = document.createElement("p");
                p.textContent = name;
                div.appendChild(p);
                div.addEventListener("click", async () => {
                    closeClientPrompt();
                    try {
                        const r = await fetch("/api/play", {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ client: name }),
                        });
                        if (!r.ok) {
                            const data = await r.json();
                            showError(data.error || "Playback failed.");
                        }
                    } catch {
                        showError("Could not reach the server.");
                    }
                });
                listEl.appendChild(div);
            });
        }
    } catch {
        const msg = document.createElement("p");
        msg.className = "no-clients-msg";
        msg.textContent = "Could not fetch client list.";
        listEl.appendChild(msg);
    }

    document.getElementById("client_prompt").classList.remove("hidden");
});

async function checkPlexStatus() {
    const badge = document.getElementById("plex-status");
    try {
        const res = await fetch("/api/status");
        const data = await res.json();
        badge.classList.toggle("online", data.ok);
        badge.classList.toggle("offline", !data.ok);
        badge.title = data.ok ? "Plex is reachable" : (data.error || "Plex is unreachable");
    } catch {
        badge.classList.remove("online");
        badge.classList.add("offline");
        badge.title = "Could not reach app server";
    }
}

checkPlexStatus();
setInterval(checkPlexStatus, 60000);

document.getElementById("btn_filters").addEventListener("click", () => {
    document.getElementById("filter_panel").classList.toggle("hidden");
});

document.getElementById("filter_genre").addEventListener("change", e => {
    filterState.genre = e.target.value;
    updateFilterButton();
});

document.getElementById("filter_year_min").addEventListener("change", e => {
    filterState.year_min = e.target.value ? parseInt(e.target.value) : null;
    updateFilterButton();
});

document.getElementById("filter_year_max").addEventListener("change", e => {
    filterState.year_max = e.target.value ? parseInt(e.target.value) : null;
    updateFilterButton();
});

document.getElementById("filter_rating_min").addEventListener("change", e => {
    filterState.rating_min = e.target.value ? parseFloat(e.target.value) : null;
    updateFilterButton();
});

document.getElementById("btn_clear_filters").addEventListener("click", () => {
    filterState.genre = "";
    filterState.year_min = null;
    filterState.year_max = null;
    filterState.rating_min = null;
    document.getElementById("filter_genre").value = "";
    document.getElementById("filter_year_min").value = "";
    document.getElementById("filter_year_max").value = "";
    document.getElementById("filter_rating_min").value = "";
    updateFilterButton();
});

loadFilters();
loadMovie();
