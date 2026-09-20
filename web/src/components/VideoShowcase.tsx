import { videoHasMedia, type Video } from "../data/videos";
import { AGENTS_BY_SLUG } from "../data/agents";

export function VideoCard({ video }: { video: Video }) {
  const ready = videoHasMedia(video);
  return (
    <div className={`card video-card${video.featured ? " featured" : ""}`}>
      <div className="video-frame">
        {ready && video.embedUrl ? (
          <iframe title={video.title} src={video.embedUrl} allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowFullScreen />
        ) : ready && video.src ? (
          <video controls playsInline preload="metadata" poster={video.thumbnail} src={video.src} />
        ) : (
          <div className="video-placeholder">
            <div className="eyebrow">Awaiting recording</div>
            <div>{video.title}</div>
            {video.duration ? <div className="muted">{video.duration}</div> : <div className="muted">A recording of this run has not been added yet.</div>}
          </div>
        )}
      </div>
      <h2 style={{ textTransform: "none", letterSpacing: 0, color: "var(--text)", fontSize: 18 }}>{video.title}</h2>
      <p>{video.description}</p>
      <p className="muted">
        {video.duration ? `${video.duration} · ` : ""}
        {video.processes.join(" · ")}
      </p>
      <p className="muted">Agents: {video.agents.map((slug) => AGENTS_BY_SLUG[slug]?.name.replace(/ Agent$/, "")).join(" · ")}</p>
    </div>
  );
}

export function VideoShowcase({ videos, heading = true }: { videos: Video[]; heading?: boolean }) {
  return (
    <section className="showcase-section" id="videos">
      {heading ? (
        <>
          <div className="eyebrow">See Maximor in action</div>
          <h2 className="section-title">Recorded office runs</h2>
          <p className="lede">
            Cuts from the Golden September desk. A valid bill is not a payment. Harbor memory does not paste last month's number. $12.40 keeps the lock open.
          </p>
        </>
      ) : null}
      <div className="grid-2">
        {videos.map((video) => (
          <VideoCard key={video.id} video={video} />
        ))}
      </div>
    </section>
  );
}
