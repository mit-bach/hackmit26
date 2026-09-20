import { RestHead } from "../components/rest/RestHead";
import { VideoShowcase } from "../components/VideoShowcase";
import { VIDEOS } from "../data/videos";

const STAKE = "Cards are placeholders until a real file exists.";

export default function Videos(): JSX.Element {
  return (
    <div className="rest-page rest-videos">
      <RestHead title="Recordings" stake={STAKE} />
      <VideoShowcase videos={VIDEOS} heading={false} />
    </div>
  );
}
