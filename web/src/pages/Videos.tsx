import { RestHead } from "../components/rest/RestHead";
import { VideoShowcase } from "../components/VideoShowcase";
import { VIDEOS } from "../data/videos";

const STAKE = "Cuts from golden-20260920-r1. September is not CLOSED. Acme was not paid.";

export default function Videos(): JSX.Element {
  return (
    <div className="rest-page rest-videos">
      <RestHead title="Recordings" stake={STAKE} />
      <VideoShowcase videos={VIDEOS} heading={false} />
    </div>
  );
}
