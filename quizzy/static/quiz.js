async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    credentials: "same-origin",
    ...options,
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const msg = data && data.error ? data.error : `HTTP ${res.status}`;
    throw new Error(msg);
  }
  return data;
}

const els = {
  prompt: document.getElementById("prompt"),
  choices: document.getElementById("choices"),
  status: document.getElementById("status"),
  streak: document.getElementById("streak"),
  globalBest: document.getElementById("globalBest"),
  nextBtn: document.getElementById("nextBtn"),
};

let currentQuestionId = null;
let busy = false;
let answered = false;
let lastCorrectAnswer = null;

function setBusy(v) {
  busy = v;
  els.nextBtn.disabled = v || !answered;
  for (const btn of els.choices.querySelectorAll("button")) {
    btn.disabled = v;
  }
}

function renderCounters(streak, globalBest) {
  if (typeof streak === "number") els.streak.textContent = String(streak);
  if (typeof globalBest === "number") els.globalBest.textContent = String(globalBest);
}

function renderQuestion(q) {
  currentQuestionId = q.question_id;
  answered = false;
  lastCorrectAnswer = null;
  els.nextBtn.disabled = true;
  els.nextBtn.textContent = "Ny fråga";

  els.prompt.textContent = q.prompt || "(ingen fråga)";
  els.choices.innerHTML = "";

  const choices = Array.isArray(q.choices) ? q.choices : [];
  for (const c of choices) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "choice";
    btn.dataset.choice = c;
    btn.textContent = c;
    btn.addEventListener("click", () => submitAnswer(c));
    els.choices.appendChild(btn);
  }

  renderCounters(q.streak, q.global_best);
}

async function startSession() {
  try {
    const data = await api("/api/quiz/session/start", { method: "POST", body: "{}" });
    renderCounters(data.streak, data.global_best);
  } catch (e) {
    // Session start failing shouldn't block basic UI; still try to proceed.
    els.status.textContent = "Kunde inte starta session.";
  }
}

async function loadNextQuestion() {
  if (busy) return;
  setBusy(true);
  els.status.textContent = "";

  try {
    const q = await api("/api/quiz/question/next");
    if (q.error) {
      els.prompt.textContent = "Fel vid hämtning av fråga.";
      els.status.textContent = q.details || q.error;
      renderCounters(q.streak, q.global_best);
    } else {
      renderQuestion(q);
    }
  } catch (e) {
    els.prompt.textContent = "Fel vid hämtning av fråga.";
    els.status.textContent = e.message;
  } finally {
    setBusy(false);
  }
}

function revealCorrectness({ correctAnswer, yourAnswer }) {
  const buttons = Array.from(els.choices.querySelectorAll("button.choice"));
  for (const b of buttons) {
    const value = b.dataset.choice;
    if (value === correctAnswer) {
      b.classList.add("correct");
    }
    if (value === yourAnswer && yourAnswer !== correctAnswer) {
      b.classList.add("wrong");
    }
  }
}

async function submitAnswer(answer) {
  if (busy) return;
  if (!currentQuestionId) return;
  if (answered) return;

  setBusy(true);
  els.status.textContent = "";

  try {
    const res = await api("/api/quiz/question/answer", {
      method: "POST",
      body: JSON.stringify({ question_id: currentQuestionId, answer }),
    });

    answered = true;
    lastCorrectAnswer = res.correct_answer || null;

    els.nextBtn.textContent = "Fortsätt";

    if (res.correct) {
      els.status.textContent = "Rätt!";
    } else {
      els.status.textContent = `Fel! Rätt svar: ${res.correct_answer}`;
    }

    revealCorrectness({ correctAnswer: res.correct_answer, yourAnswer: res.your_answer });

    renderCounters(res.streak, res.global_best);

    // Wait for the user to proceed
    els.nextBtn.disabled = false;
    setBusy(false);
  } catch (e) {
    els.status.textContent = e.message;
  } finally {
    // If we answered successfully we already cleared busy above
    if (!answered) setBusy(false);
  }
}

els.nextBtn.addEventListener("click", () => loadNextQuestion());

(async function main() {
  await startSession();
  await loadNextQuestion();
})();
