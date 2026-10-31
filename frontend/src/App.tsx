import { useEffect, useState } from "react";
import "./App.css";

const API = "http://127.0.0.1:8000";

type Run = {
  id: string;
  model_name: string;
  provider: string;
  status: "passed" | "failed";
  score: number;
  latency_ms: number;
  input_tokens: number | null;
  output_tokens: number | null;
  evaluated_at: string;
  prompt?: string;
  response?: string;
};

type Metrics = {
  sample_size: number;
  average_score: number | null;
  pass_rate: number | null;
  average_latency_ms: number | null;
  known_input_tokens: number;
  known_output_tokens: number;
};

type Summary = {
  model: string;
  completed: number;
  failed_requests: number;
  average_score: number | null;
  average_latency_ms: number | null;
  input_tokens: number;
  output_tokens: number;
};

type BenchmarkResponse = {
  summary: Summary[];
  results: Run[];
  errors: { model: string; case_index: number; error: string }[];
};

const percent = (value: number | null) =>
  value === null ? "—" : `${(value * 100).toFixed(1)}%`;

function App() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [runs, setRuns] = useState<Run[]>([]);
  const [benchmark, setBenchmark] = useState<BenchmarkResponse | null>(null);
  const [models, setModels] = useState("model-alpha, model-beta");
  const [prompt, setPrompt] = useState("Explain AWS cloud computing");
  const [terms, setTerms] = useState("AWS, cloud");
  const [loading, setLoading] = useState(false);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState("");
  const [tab, setTab] = useState<"overview" | "benchmark" | "history">(
    "overview",
  );

  async function refresh() {
    try {
      const [m, r] = await Promise.all([
        fetch(`${API}/api/v1/metrics`),
        fetch(`${API}/api/v1/runs?limit=100`),
      ]);

      if (!m.ok || !r.ok) throw new Error("API request failed");

      setMetrics(await m.json());
      setRuns(await r.json());
      setConnected(true);
      setError("");
    } catch {
      setConnected(false);
      setError("Cannot reach FastAPI. Check that port 8000 is running.");
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function runBenchmark() {
    const modelList = models
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    const termList = terms
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);

    if (modelList.length < 1 || modelList.length > 3) {
      setError("Choose between one and three models.");
      return;
    }
    if (new Set(modelList).size !== modelList.length) {
      setError("Model names must be unique.");
      return;
    }
    if (!prompt.trim()) {
      setError("Enter a benchmark prompt.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API}/api/v1/benchmarks`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          provider: "mock",
          models: modelList,
          cases: [{ prompt: prompt.trim(), expected_terms: termList }],
        }),
      });

      if (!response.ok) {
        const detail = await response.text();
        throw new Error(`Benchmark failed (${response.status}): ${detail}`);
      }

      const result: BenchmarkResponse = await response.json();
      setBenchmark(result);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  const navigation = [
    { id: "overview", label: "Overview", icon: "◫" },
    { id: "benchmark", label: "AI Benchmarks", icon: "◇" },
    { id: "history", label: "Evaluation History", icon: "≡" },
  ] as const;

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">C</div>
          <div>
            <strong>CloudForge</strong>
            <small>AI OPERATIONS</small>
          </div>
        </div>

        <p className="nav-label">WORKSPACE</p>
        <nav>
          {navigation.map((item) => (
            <button
              key={item.id}
              className={`nav-button ${tab === item.id ? "active" : ""}`}
              onClick={() => setTab(item.id)}
            >
              <span className="nav-icon">{item.icon}</span>
              {item.label}
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <span className={`status-dot ${connected ? "online" : ""}`} />
          {connected ? "Backend connected" : "Backend offline"}
          <small>Local development • Phase 4</small>
        </div>
      </aside>

      <main className="main">
        <header className="header">
          <div>
            <p className="eyebrow">CLOUDFORGE / WORKSPACE</p>
            <h1>
              {tab === "overview"
                ? "Operations Overview"
                : tab === "benchmark"
                  ? "AI Benchmark Lab"
                  : "Evaluation History"}
            </h1>
            <p className="subtitle">
              Monitor, evaluate, and compare AI workloads.
            </p>
          </div>
          <button className="secondary-button" onClick={() => void refresh()}>
            ↻ Refresh data
          </button>
        </header>

        {error && <div className="error">{error}</div>}

        {tab === "overview" && (
          <>
            <section className="stats">
              <Stat
                label="Total Evaluations"
                value={metrics?.sample_size.toString() ?? "—"}
                note="Recent stored runs"
              />
              <Stat
                label="Average Score"
                value={percent(metrics?.average_score ?? null)}
                note="Keyword coverage"
              />
              <Stat
                label="Pass Rate"
                value={percent(metrics?.pass_rate ?? null)}
                note="All terms matched"
              />
              <Stat
                label="Average Latency"
                value={
                  metrics?.average_latency_ms == null
                    ? "—"
                    : `${metrics.average_latency_ms.toFixed(1)} ms`
                }
                note="Recorded provider latency"
              />
            </section>

            <section className="two-column">
              <div className="panel">
                <div className="panel-heading">
                  <div>
                    <h2>Evaluation Scores</h2>
                    <p>Most recent evaluation results</p>
                  </div>
                </div>
                {runs.length === 0 ? (
                  <Empty />
                ) : (
                  <div className="score-list">
                    {runs.slice(0, 8).map((run) => (
                      <div key={run.id} className="score-item">
                        <span>{run.model_name}</span>
                        <div className="bar-track">
                          <div
                            className="bar-fill"
                            style={{ width: `${run.score * 100}%` }}
                          />
                        </div>
                        <strong>{percent(run.score)}</strong>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="panel">
                <div className="panel-heading">
                  <div>
                    <h2>Usage Analytics</h2>
                    <p>Reported token consumption</p>
                  </div>
                </div>
                <div className="usage-value">
                  {(
                    (metrics?.known_input_tokens ?? 0) +
                    (metrics?.known_output_tokens ?? 0)
                  ).toLocaleString()}
                </div>
                <p className="muted">Total known tokens</p>
                <div className="usage-grid">
                  <div>
                    <span>Input</span>
                    <strong>{metrics?.known_input_tokens ?? 0}</strong>
                  </div>
                  <div>
                    <span>Output</span>
                    <strong>{metrics?.known_output_tokens ?? 0}</strong>
                  </div>
                </div>
                <p className="hint">Mock provider usage may be unavailable.</p>
              </div>
            </section>

            <section className="panel">
              <div className="panel-heading">
                <div>
                  <h2>Recent Activity</h2>
                  <p>Latest evaluations stored in SQLite</p>
                </div>
                <button
                  className="text-button"
                  onClick={() => setTab("history")}
                >
                  View all →
                </button>
              </div>
              <RunTable runs={runs.slice(0, 5)} />
            </section>
          </>
        )}

        {tab === "benchmark" && (
          <section className="two-column benchmark-layout">
            <div className="panel">
              <div className="panel-heading">
                <div>
                  <h2>Run a Benchmark</h2>
                  <p>Compare simulated models locally</p>
                </div>
              </div>

              <label>Model names (comma separated)</label>
              <input
                value={models}
                onChange={(e) => setModels(e.target.value)}
              />

              <label>Evaluation prompt</label>
              <textarea
                rows={5}
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
              />

              <label>Expected terms (comma separated)</label>
              <input value={terms} onChange={(e) => setTerms(e.target.value)} />

              <button
                className="primary-button"
                disabled={loading || !connected}
                onClick={() => void runBenchmark()}
              >
                {loading ? "Running evaluation..." : "Run Benchmark →"}
              </button>
              <p className="hint">
                Uses the mock provider. No API key or AWS billing required.
              </p>
            </div>

            <div className="panel">
              <div className="panel-heading">
                <div>
                  <h2>Model Comparison</h2>
                  <p>Results from the latest benchmark</p>
                </div>
              </div>
              {!benchmark ? (
                <Empty message="Run a benchmark to see model comparisons." />
              ) : (
                <>
                  {benchmark.summary.map((model) => (
                    <div className="comparison-card" key={model.model}>
                      <div className="comparison-top">
                        <strong>{model.model}</strong>
                        <span>{percent(model.average_score)}</span>
                      </div>
                      <div className="bar-track">
                        <div
                          className="bar-fill"
                          style={{
                            width: `${(model.average_score ?? 0) * 100}%`,
                          }}
                        />
                      </div>
                      <div className="comparison-footer">
                        <span>{model.completed} completed</span>
                        <span>{model.failed_requests} errors</span>
                        <span>{model.average_latency_ms ?? "—"} ms</span>
                      </div>
                    </div>
                  ))}
                  {benchmark.errors.length > 0 && (
                    <p className="error">
                      {benchmark.errors.length} benchmark requests failed.
                    </p>
                  )}
                  <p className="hint">
                    Keyword coverage is not a measure of semantic model quality.
                  </p>
                </>
              )}
            </div>
          </section>
        )}

        {tab === "history" && (
          <section className="panel">
            <div className="panel-heading">
              <div>
                <h2>Evaluation History</h2>
                <p>Up to 100 recent saved evaluations</p>
              </div>
            </div>
            <RunTable runs={runs} />
          </section>
        )}

        <footer className="footer">
          CloudForge AI • Local MLOps development environment
        </footer>
      </main>
    </div>
  );
}

function Stat({
  label,
  value,
  note,
}: {
  label: string;
  value: string;
  note: string;
}) {
  return (
    <div className="stat-card">
      <p>{label}</p>
      <strong>{value}</strong>
      <small>{note}</small>
    </div>
  );
}

function Empty({
  message = "No evaluations yet. Run a benchmark to populate this view.",
}: {
  message?: string;
}) {
  return <div className="empty">{message}</div>;
}

function RunTable({ runs }: { runs: Run[] }) {
  if (runs.length === 0) return <Empty />;

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Model</th>
            <th>Provider</th>
            <th>Score</th>
            <th>Status</th>
            <th>Latency</th>
            <th>Date</th>
          </tr>
        </thead>
        <tbody>
          {runs.map((run) => (
            <tr key={run.id}>
              <td className="model-name">{run.model_name}</td>
              <td>{run.provider}</td>
              <td>{percent(run.score)}</td>
              <td>
                <span className={`pill ${run.status}`}>{run.status}</span>
              </td>
              <td>{run.latency_ms.toFixed(1)} ms</td>
              <td>{new Date(run.evaluated_at).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default App;
