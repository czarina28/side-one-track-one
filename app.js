let currentAlbum = null;
let answered = false;
let score = 0;
let rounds = 0;

const albumTitle = document.getElementById("album");
const artistDisplay = document.getElementById("artist");
const yearDisplay = document.getElementById("year");
const result = document.getElementById("result");
const nextButton = document.getElementById("next");
const scoreDisplay = document.getElementById("score");

const form = document.querySelector("form");
const oldAnswer = document.getElementById("answer");
const oldSubmit = form ? form.querySelector('button[type="submit"]') : null;

// We no longer use free-text answers.
if (oldAnswer) oldAnswer.style.display = "none";
if (oldSubmit) oldSubmit.style.display = "none";

const choicesContainer = document.createElement("div");
choicesContainer.className = "choices";

if (form) {
    form.appendChild(choicesContainer);
}


function shuffle(array) {
    const copy = [...array];

    for (let i = copy.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));

        [copy[i], copy[j]] = [
            copy[j],
            copy[i]
        ];
    }

    return copy;
}


function cleanTrackPool(album) {
    const correct = album.opening_track;

    // Remove duplicate titles and the correct answer.
    //
    // Also avoid obvious edition junk where possible.
    const tracks = album.tracks.filter(track => {
        if (!track) return false;

        if (track === correct) return false;

        const lower = track.toLowerCase();

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
    const correct = album.opening_track;
    const pool = cleanTrackPool(album);

    const wrong = shuffle(pool).slice(0, 3);

    /*
     * In the unlikely event an album has fewer than three
     * usable distractors, borrow tracks from other albums.
     */
    if (wrong.length < 3) {
        const fallback = [];

        for (const otherAlbum of ALBUMS) {
            if (otherAlbum === album) continue;

            for (const track of otherAlbum.tracks) {
                if (
                    track &&
                    track !== correct &&
                    !wrong.includes(track)
                ) {
                    fallback.push(track);
                }
            }
        }

        const extras = shuffle(fallback);

        while (
            wrong.length < 3 &&
            extras.length
        ) {
            const candidate = extras.pop();

            if (!wrong.includes(candidate)) {
                wrong.push(candidate);
            }
        }
    }

    return shuffle([
        correct,
        ...wrong
    ]);
}


function renderChoices(album) {
    choicesContainer.innerHTML = "";

    const choices = getChoices(album);

    choices.forEach((track, index) => {
        const button = document.createElement("button");

        button.type = "button";
        button.className = "choice";
        button.dataset.track = track;

        button.textContent =
            `${index + 1}. ${track}`;

        button.addEventListener("click", () => {
            chooseAnswer(button);
        });

        choicesContainer.appendChild(button);
    });
}


function chooseAnswer(selectedButton) {
    if (answered) return;

    answered = true;
    rounds++;

    const selectedTrack =
        selectedButton.dataset.track;

    const correctTrack =
        currentAlbum.opening_track;

    const buttons =
        choicesContainer.querySelectorAll(".choice");

    buttons.forEach(button => {
        button.disabled = true;

        if (
            button.dataset.track === correctTrack
        ) {
            button.classList.add(
                "choice-correct"
            );
        }
    });

    if (selectedTrack === correctTrack) {
        score++;

        result.textContent = "CORRECT";
    } else {
        selectedButton.classList.add(
            "choice-wrong"
        );

        result.textContent =
            `SIDE ONE, TRACK ONE: ${correctTrack}`;
    }

    updateScore();

    nextButton.style.display = "inline-block";
}


function updateScore() {
    if (!scoreDisplay) return;

    scoreDisplay.textContent =
        `${score} / ${rounds}`;
}


function newAlbum() {
    answered = false;

    let nextAlbum;

    // Avoid immediately repeating the same album.
    do {
        nextAlbum =
            ALBUMS[
                Math.floor(
                    Math.random() * ALBUMS.length
                )
            ];
    } while (
        ALBUMS.length > 1 &&
        nextAlbum === currentAlbum
    );

    currentAlbum = nextAlbum;

   albumTitle.textContent = currentAlbum.album;
artistDisplay.textContent = currentAlbum.artist;
yearDisplay.textContent = currentAlbum.year || "";

    result.textContent = "";

    nextButton.style.display = "none";

    renderChoices(currentAlbum);
}


nextButton.addEventListener(
    "click",
    newAlbum
);


document.addEventListener(
    "keydown",
    event => {

        if (
            !answered &&
            ["1", "2", "3", "4"].includes(event.key)
        ) {
            const index =
                Number(event.key) - 1;

            const buttons =
                choicesContainer.querySelectorAll(".choice");

            if (buttons[index]) {
                buttons[index].click();
            }

            return;
        }

        if (
            answered &&
            event.key === "Enter"
        ) {
            newAlbum();
        }
    }
);


updateScore();
newAlbum();