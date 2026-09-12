let currentAlbum = null;
let answered = false;
let score = 0;
let rounds = 0;
let albumDeck = [];
let misses = 0;
let gameOver = false;
let currentOddTrack = null;
let currentOddAlbum = null;
let timelineAlbums = [];
let timelinePicks = [];
let roundTypeDeck = [];
const MAX_MISSES = 4;

const albumTitle = document.getElementById("album");
const artistDisplay = document.getElementById("artist");
const yearDisplay = document.getElementById("year");
const result = document.getElementById("result");
const nextButton = document.getElementById("next");
const scoreDisplay = document.getElementById("score");
const choicesContainer = document.getElementById("choices");
const roundLabel = document.getElementById("round-label");
const questionLabel = document.getElementById("question-label");
const timelineActions = document.getElementById("timeline-actions");
const deselectButton = document.getElementById("deselect");
const submitOrderButton = document.getElementById("submit-order");

function shuffle(array) {
    const copy = [...array];
    for (let i = copy.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [copy[i], copy[j]] = [copy[j], copy[i]];
    }
    return copy;
}

function cleanTrackPool(album) {
    const tracks = album.tracks.filter(track => {
        if (!track) return false;
        const lower = track.toLowerCase();
        if (lower.includes("documentary")) return false;
        if (lower.includes("remix")) return false;
        if (lower.includes("demo")) return false;
        if (lower.includes("live")) return false;
        if (lower.includes("session")) return false;
        if (lower.includes("alternate")) return false;
        if (lower.includes("version")) return false;
        if (lower.includes("mix)")) return false;
        return true;
    });
    return [...new Set(tracks)];
}

function getChoices(album) {
    const albumTracks = cleanTrackPool(album);
    const onAlbum = shuffle(albumTracks).slice(0, 3);
    const albumTrackNames = new Set(album.tracks.map(track => track.toLowerCase()));

    // Prefer a song by the same artist from a different album. If the pool has
    // only one album by that artist, use a clean track from another record.
    const sameArtist = ALBUMS.filter(other =>
        other !== album && other.artist === album.artist
    );
    const otherAlbums = sameArtist.length
        ? sameArtist
        : ALBUMS.filter(other => other !== album);
    const outsiderPool = otherAlbums.flatMap(other =>
        cleanTrackPool(other).map(track => ({ track, album: other }))
    ).filter(candidate =>
        !albumTrackNames.has(candidate.track.toLowerCase()) &&
        !onAlbum.includes(candidate.track)
    );

    const outsider = shuffle(outsiderPool)[0];
    currentOddTrack = outsider.track;
    currentOddAlbum = outsider.album;
    return shuffle([...onAlbum, currentOddTrack]);
}

function outsiderReveal() {
    return `${currentOddTrack} · FROM ${currentOddAlbum.album} BY ${currentOddAlbum.artist}`;
}

function renderChoices(album) {
    choicesContainer.innerHTML = "";
    getChoices(album).forEach((track, index) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "choice";
        button.dataset.track = track;
        button.textContent = `${index + 1}. ${track}`;
        button.addEventListener("click", () => chooseAnswer(button));
        choicesContainer.appendChild(button);
    });
}

function renderOpeningTrackChoices(album) {
    choicesContainer.innerHTML = "";
    const correct = album.opening_track;
    const otherTracks = cleanTrackPool(album).filter(track => track !== correct);
    const choices = shuffle([correct, ...shuffle(otherTracks).slice(0, 3)]);

    choices.forEach((track, index) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "choice";
        button.dataset.track = track;
        button.textContent = `${index + 1}. ${track}`;
        button.addEventListener("click", () => chooseOpeningTrack(button));
        choicesContainer.appendChild(button);
    });
}

function chooseOpeningTrack(selectedButton) {
    if (answered) return;
    answered = true;
    rounds++;

    const selectedTrack = selectedButton.dataset.track;
    const correctTrack = currentAlbum.opening_track;

    choicesContainer.querySelectorAll(".choice").forEach(button => {
        button.disabled = true;
        if (button.dataset.track === correctTrack) {
            button.classList.add("choice-correct");
        }
    });

    if (selectedTrack === correctTrack) {
        score++;
        finishRound(`CORRECT · SIDE ONE, TRACK ONE: ${correctTrack}`);
    } else {
        score--;
        misses++;
        selectedButton.classList.add("choice-wrong");
        finishRound(`SIDE ONE, TRACK ONE: ${correctTrack}`);
    }
}

function renderTimelineChoices() {
    choicesContainer.innerHTML = "";
    timelinePicks = [];

    timelineAlbums.forEach((album, index) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "choice timeline-choice";
        button.dataset.index = index;
        button.dataset.label = `${album.album} · ${album.artist}`;
        button.textContent = button.dataset.label;
        button.addEventListener("click", () => chooseTimelineAlbum(button));
        choicesContainer.appendChild(button);
    });
}

function chooseTimelineAlbum(button) {
    if (answered || button.classList.contains("timeline-selected")) return;

    timelinePicks.push(Number(button.dataset.index));
    button.classList.add("timeline-selected");
    button.textContent = `${timelinePicks.length}. ${button.dataset.label}`;
    deselectButton.disabled = false;
    submitOrderButton.disabled = timelinePicks.length < timelineAlbums.length;
}

function deselectLastTimelineAlbum() {
    if (answered || timelinePicks.length === 0) return;

    const removedIndex = timelinePicks.pop();
    const button = choicesContainer.querySelector(`[data-index="${removedIndex}"]`);
    if (button) {
        button.classList.remove("timeline-selected");
        button.textContent = button.dataset.label;
    }

    deselectButton.disabled = timelinePicks.length === 0;
    submitOrderButton.disabled = true;
}

function submitTimelineOrder() {
    if (answered || timelinePicks.length < timelineAlbums.length) return;

    answered = true;
    rounds++;
    const correctOrder = timelineAlbums
        .map((album, index) => ({ album, index }))
        .sort((a, b) => a.album.year - b.album.year);
    const correct = timelinePicks.every((picked, position) =>
        picked === correctOrder[position].index
    );

    choicesContainer.querySelectorAll(".choice").forEach(choice => {
        choice.disabled = true;
    });
    deselectButton.disabled = true;
    submitOrderButton.disabled = true;

    const timeline = correctOrder
        .map(item => `${item.album.album} (${item.album.year})`)
        .join(" → ");

    if (correct) {
        score++;
        finishRound(`CORRECT · ${timeline}`);
    } else {
        score--;
        misses++;
        finishRound(`CORRECT ORDER: ${timeline}`);
    }
}

function finishRound(message) {
    result.textContent = message;
    updateScore();

    if (misses >= MAX_MISSES) {
        gameOver = true;
        result.textContent = `GAME OVER · FINAL SCORE: ${score} · ${message}`;
        nextButton.textContent = "NEW GAME ›";
    } else {
        nextButton.textContent = "NEXT ROUND ›";
    }

    nextButton.classList.remove("hidden");
}

function chooseAnswer(selectedButton) {
    if (answered) return;
    answered = true;
    rounds++;

    const selectedTrack = selectedButton.dataset.track;
    const correctTrack = currentOddTrack;
    const buttons = choicesContainer.querySelectorAll(".choice");

    buttons.forEach(button => {
        button.disabled = true;
        if (button.dataset.track === correctTrack) {
            button.classList.add("choice-correct");
        }
    });

    if (selectedTrack === correctTrack) {
        score++;
        result.textContent = `CORRECT · ${outsiderReveal()}`;
    } else {
        score--;
        misses++;
        selectedButton.classList.add("choice-wrong");
        result.textContent = `NOT ON THIS ALBUM: ${outsiderReveal()}`;
    }

    finishRound(result.textContent);
}

function updateScore() {
    scoreDisplay.textContent = `SCORE ${score} · MISSES ${misses} / ${MAX_MISSES}`;
}

function startNewGame() {
    score = 0;
    rounds = 0;
    misses = 0;
    gameOver = false;
    albumDeck = [];
    currentAlbum = null;
    roundTypeDeck = [];
    updateScore();
    newAlbum();
}

function newAlbum() {
    answered = false;

    if (roundTypeDeck.length === 0) {
        roundTypeDeck = shuffle([
            "intruder", "intruder", "intruder", "intruder",
            "timeline", "timeline", "timeline", "timeline",
            "opening", "opening"
        ]);
    }

    const roundType = roundTypeDeck.pop();
    if (roundType === "timeline") {
        renderTimelineRound();
    } else if (roundType === "opening") {
        renderOpeningTrackRound();
    } else {
        renderIntruderRound();
    }
}

function renderIntruderRound() {

    if (albumDeck.length === 0) {
        albumDeck = shuffle(ALBUMS);

        // When a fresh deck begins, avoid dealing the previous album again.
        if (albumDeck.length > 1 && albumDeck[albumDeck.length - 1] === currentAlbum) {
            [albumDeck[0], albumDeck[albumDeck.length - 1]] =
                [albumDeck[albumDeck.length - 1], albumDeck[0]];
        }
    }

    currentAlbum = albumDeck.pop();
    roundLabel.textContent = "ALBUM · FIND THE INTRUDER";
    questionLabel.innerHTML = 'WHICH SONG <span class="question-emphasis">WASN\'T</span> ON THIS ALBUM?';
    albumTitle.textContent = currentAlbum.album;
    artistDisplay.textContent = currentAlbum.artist;
    yearDisplay.textContent = currentAlbum.year || "";
    result.textContent = "";
    timelineActions.classList.add("hidden");
    nextButton.classList.add("hidden");
    renderChoices(currentAlbum);
}

function renderTimelineRound() {
    const candidates = shuffle(ALBUMS);
    timelineAlbums = [];
    const usedYears = new Set();

    for (const album of candidates) {
        if (!usedYears.has(album.year)) {
            timelineAlbums.push(album);
            usedYears.add(album.year);
        }
        if (timelineAlbums.length === 4) break;
    }

    roundLabel.textContent = "ALBUM TIMELINE";
    questionLabel.textContent = "TAP EARLIEST TO LATEST";
    albumTitle.textContent = "PUT THEM IN ORDER";
    artistDisplay.textContent = "";
    yearDisplay.textContent = "";
    result.textContent = "";
    timelineActions.classList.remove("hidden");
    deselectButton.disabled = true;
    submitOrderButton.disabled = true;
    nextButton.classList.add("hidden");
    renderTimelineChoices();
}

function renderOpeningTrackRound() {
    if (albumDeck.length === 0) {
        albumDeck = shuffle(ALBUMS);
    }

    currentAlbum = albumDeck.pop();
    roundLabel.textContent = "SIDE ONE · TRACK ONE";
    questionLabel.textContent = "WHICH SONG OPENS THE ALBUM?";
    albumTitle.textContent = currentAlbum.album;
    artistDisplay.textContent = currentAlbum.artist;
    yearDisplay.textContent = currentAlbum.year;
    result.textContent = "";
    timelineActions.classList.add("hidden");
    nextButton.classList.add("hidden");
    renderOpeningTrackChoices(currentAlbum);
}

deselectButton.addEventListener("click", deselectLastTimelineAlbum);
submitOrderButton.addEventListener("click", submitTimelineOrder);

nextButton.addEventListener("click", () => {
    if (gameOver) {
        startNewGame();
    } else {
        newAlbum();
    }
});

document.addEventListener("keydown", event => {
    if (!answered && ["1", "2", "3", "4"].includes(event.key)) {
        const index = Number(event.key) - 1;
        const buttons = choicesContainer.querySelectorAll(".choice");
        if (buttons[index]) buttons[index].click();
        return;
    }

    if (answered && event.key === "Enter") {
        if (gameOver) {
            startNewGame();
        } else {
            newAlbum();
        }
    }
});

updateScore();
newAlbum();
