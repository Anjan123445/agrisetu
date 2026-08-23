import { useRef, useState } from "react";
import PageShell from "../components/Layout";
import FurrowDivider from "../components/FurrowDivider";
import { useApp } from "../context/AppContext";
import { getVoiceQuery } from "../api/api";
import { ErrorState } from "./AdvisoryDashboard";

export default function VoiceQuery() {
  const { t, language } = useApp();
  const [status, setStatus] = useState("idle"); // idle | recording | processing | done
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [playing, setPlaying] = useState(false);

  const mediaRecorder = useRef(null);
  const chunks = useRef([]);
  const audioRef = useRef(null);

  async function startRecording() {
    setError(null);
    setResult(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      chunks.current = [];
      recorder.ondataavailable = (e) => chunks.current.push(e.data);
      recorder.onstop = handleStop;
      recorder.start();
      mediaRecorder.current = recorder;
      setStatus("recording");
    } catch {
      setError(t.errorGeneric);
    }
  }

  function stopRecording() {
    mediaRecorder.current?.stop();
    mediaRecorder.current?.stream.getTracks().forEach((track) => track.stop());
  }

  async function handleStop() {
    setStatus("processing");
    const blob = new Blob(chunks.current, { type: "audio/webm" });
    try {
      const res = await getVoiceQuery({ audio: blob, language });
      setResult(res);
      setStatus("done");
    } catch {
      setError(t.errorGeneric);
      setStatus("idle");
    }
  }

  function togglePlay() {
    if (!audioRef.current) return;
    if (playing) {
      audioRef.current.pause();
    } else {
      audioRef.current.play().catch(() => {});
    }
    setPlaying(!playing);
  }

  return (
    <PageShell showBack>
      <section className="mx-auto max-w-xl px-5 py-6 sm:px-8">
        <h1 className="font-display text-2xl font-semibold text-leaf-deep sm:text-3xl">
          {t.voiceTitle}
        </h1>
        <p className="mt-2 text-sm leading-relaxed text-ink/70">{t.voiceBody}</p>

        <div className="mt-10 flex flex-col items-center">
          <button
            type="button"
            onPointerDown={status === "idle" || status === "done" ? startRecording : undefined}
            onPointerUp={status === "recording" ? stopRecording : undefined}
            onPointerLeave={status === "recording" ? stopRecording : undefined}
            disabled={status === "processing"}
            aria-pressed={status === "recording"}
            className={`flex h-28 w-28 items-center justify-center rounded-full text-4xl text-white shadow-lg transition-all active:scale-95 ${
              status === "recording"
                ? "scale-110 bg-alert shadow-alert/30"
                : "bg-leaf shadow-leaf/30 sm:hover:bg-leaf-deep"
            } ${status === "processing" ? "opacity-60" : ""}`}
          >
            <span aria-hidden="true">🎙</span>
          </button>
          <p className="mt-4 text-sm font-semibold text-ink/70">
            {status === "recording"
              ? t.voiceRecording
              : status === "processing"
                ? t.voiceProcessing
                : t.voiceTapToRecord}
          </p>
        </div>

        {error && <ErrorState message={error} />}

        {result && status === "done" && (
          <div className="mt-8 space-y-4">
            <FurrowDivider />
            <div className="rounded-2xl border border-ink/10 bg-white p-4">
              <h3 className="text-xs font-bold uppercase tracking-wide text-ink/50">
                {t.voiceTranscriptLabel}
              </h3>
              <p className="mt-1.5 text-sm italic leading-relaxed text-ink/80">
                “{result.transcript}”
              </p>
            </div>
            <div className="rounded-2xl bg-leaf-deep p-4 text-white">
              <h3 className="text-xs font-bold uppercase tracking-wide text-husk/60">
                {t.voiceResponseLabel}
              </h3>
              <p className="mt-1.5 text-sm leading-relaxed">{result.response_text}</p>
              <button
                type="button"
                onClick={togglePlay}
                className="mt-3 flex items-center gap-2 rounded-full bg-marigold px-4 py-2 text-xs font-bold text-leaf-deep active:scale-95"
              >
                <span aria-hidden="true">{playing ? "❚❚" : "▶"}</span>
                {t.voicePlayResponse}
              </button>
              <audio
                ref={audioRef}
                src={result.response_audio_url}
                onEnded={() => setPlaying(false)}
                className="hidden"
              />
            </div>
          </div>
        )}
      </section>
    </PageShell>
  );
}
