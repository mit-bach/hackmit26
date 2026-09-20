import { useState } from "react";
import { DEFAULT_HOME_EVENT, HOME_EVENTS, eventStoryById } from "../data/eventStories";
import { FlowPlay } from "./FlowPlay";

export function EventBoard(): JSX.Element {
  const [eventId, setEventId] = useState(DEFAULT_HOME_EVENT);
  const [allowAutoplay, setAllowAutoplay] = useState(true);
  const story = eventStoryById(eventId);

  function selectEvent(id: string): void {
    setEventId(id);
    setAllowAutoplay(false);
  }

  return (
    <div className="event-board-wrap">
      <div className="event-board" role="list" aria-label="Incoming events">
        {HOME_EVENTS.map((item) => {
          const active = item.id === story.id;
          return (
            <button
              key={item.id}
              type="button"
              className={active ? "event-chip active" : "event-chip"}
              aria-pressed={active}
              onClick={() => selectEvent(item.id)}
            >
              {item.label}
            </button>
          );
        })}
      </div>
      <FlowPlay
        key={story.id}
        nodes={story.nodes}
        edges={story.edges}
        steps={story.steps}
        autoplay={allowAutoplay && story.id === DEFAULT_HOME_EVENT}
      />
    </div>
  );
}
