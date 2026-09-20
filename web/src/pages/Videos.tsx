import { PageHead } from "../layout/Shell";
import { VideoShowcase } from "../components/VideoShowcase";
import { VIDEOS } from "../data/videos";

export default function Videos() {
  return (
    <div>
      <PageHead
        eyebrow="See Maximor in action"
        title="Recorded office runs"
        lede="This gallery is ready for recordings of the live office. Until a recording is added, each card is an honest placeholder — not a fake success clip."
      />
      <VideoShowcase videos={VIDEOS} heading={false} />
    </div>
  );
}
