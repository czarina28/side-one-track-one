let currentAlbum = null;
let answered = false;
let score = 0;
let rounds = 0;
let albumDeck = [];
let misses = 0;
let gameOver = false;
let currentOddTrack = null;
let currentOddAlbum = null;
const MAX_MISSES = 4;

const albumTitle = document.getElementById("album");
const artistDisplay = document.getElementById("artist");
const yearDisplay = document.getElementById("year");
const result = document.getElementById("result");
const nextButton = document.getElementById("next");
const scoreDisplay = document.getElementById("score");
const choicesContainer = document.getElementById("choices");

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

    updateScore();

    if (misses >= MAX_MISSES) {
        gameOver = true;
        result.textContent = `GAME OVER · FINAL SCORE: ${score} · ${outsiderReveal()}`;
        nextButton.textContent = "NEW GAME ›";
    } else {
        nextButton.textContent = "NEXT ALBUM ›";
    }

    nextButton.classList.remove("hidden");
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
    updateScore();
    newAlbum();
}

function newAlbum() {
    answered = false;

    if (albumDeck.length === 0) {
        albumDeck = shuffle(ALBUMS);

        // When a fresh deck begins, avoid dealing the previous album again.
        if (albumDeck.length > 1 && albumDeck[albumDeck.length - 1] === currentAlbum) {
            [albumDeck[0], albumDeck[albumDeck.length - 1]] =
                [albumDeck[albumDeck.length - 1], albumDeck[0]];
        }
    }

    currentAlbum = albumDeck.pop();
    albumTitle.textContent = currentAlbum.album;
    artistDisplay.textContent = currentAlbum.artist;
    yearDisplay.textContent = currentAlbum.year || "";
    result.textContent = "";
    nextButton.classList.add("hidden");
    renderChoices(currentAlbum);
}

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
