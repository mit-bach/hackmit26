import { render } from "@testing-library/react";
import { AgentIcon, isIconSlug } from "./AgentIcon";
import { GRAIN_SLUGS } from "../data/agents";

test("every standing agent and World has a specialized icon", () => {
  const slugs = [...GRAIN_SLUGS, "world", "event"];
  for (const slug of slugs) {
    expect(isIconSlug(slug)).toBe(true);
    const { container, unmount } = render(<AgentIcon slug={slug} />);
    expect(container.querySelector("svg")).not.toBeNull();
    unmount();
  }
});
