interface RestHeadProps {
  readonly title: string;
  readonly stake: string;
}

export function RestHead(props: RestHeadProps): JSX.Element {
  return (
    <header className="rest-head">
      <h1>{props.title}</h1>
      <p className="rest-stake">{props.stake}</p>
    </header>
  );
}
