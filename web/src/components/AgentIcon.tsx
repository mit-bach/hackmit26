import type { ReactNode } from "react";
import type { AgentSlug } from "../data/agents";

export type IconSlug = AgentSlug | "world" | "event";

export interface AgentIconProps {
  readonly slug: string;
  readonly size?: number;
  readonly className?: string;
}

interface GlyphProps {
  readonly size: number;
  readonly className?: string;
}

const STROKE = 1.65;

function SvgFrame({ size, className, children }: GlyphProps & { children: ReactNode }): JSX.Element {
  return (
    <svg
      className={className}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={STROKE}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      {children}
    </svg>
  );
}

function EmailGlyph(props: GlyphProps): JSX.Element {
  return (
    <SvgFrame {...props}>
      <rect x="3.2" y="6.2" width="17.6" height="12.2" rx="1.4" />
      <path d="M3.6 7.2 12 13.1 20.4 7.2" />
    </SvgFrame>
  );
}

function StripeGlyph(props: GlyphProps): JSX.Element {
  return (
    <SvgFrame {...props}>
      <rect x="3" y="6" width="18" height="12.5" rx="1.6" />
      <path d="M3 10.1h18" />
      <path d="M6.2 15.2h4.6" />
      <path d="M16.2 4.8 19.2 19.2" />
    </SvgFrame>
  );
}

function BankGlyph(props: GlyphProps): JSX.Element {
  return (
    <SvgFrame {...props}>
      <path d="M3.2 9.8 12 4.6l8.8 5.2" />
      <path d="M4.2 19.4h15.6" />
      <path d="M5.4 9.8h13.2v9.6" />
      <path d="M8.2 19.4v-6.2M12 19.4v-6.2M15.8 19.4v-6.2" />
    </SvgFrame>
  );
}

function BooksGlyph(props: GlyphProps): JSX.Element {
  return (
    <SvgFrame {...props}>
      <path d="M4.2 6.2c2.2 0 3.7.9 4.2 1.7V19c-.8-.8-2.3-1.6-4.2-1.6V6.2Z" />
      <path d="M19.8 6.2c-2.2 0-3.7.9-4.2 1.7V19c.8-.8 2.3-1.6 4.2-1.6V6.2Z" />
      <path d="M12 7.8V19" />
    </SvgFrame>
  );
}

function ApGlyph(props: GlyphProps): JSX.Element {
  return (
    <SvgFrame {...props}>
      <rect x="6" y="4.4" width="12" height="16.2" rx="1.4" />
      <path d="M9 4.4h6v2.4H9Z" />
      <path d="M9.1 12.3 11 14.2l3.9-4.1" />
    </SvgFrame>
  );
}

function PayGlyph(props: GlyphProps): JSX.Element {
  return (
    <SvgFrame {...props}>
      <rect x="3.2" y="6.8" width="17.6" height="11" rx="1.4" />
      <circle cx="12" cy="12.3" r="2.4" />
      <path d="M6.2 9.6v5.4M17.8 9.6v5.4" />
    </SvgFrame>
  );
}

function ApplyGlyph(props: GlyphProps): JSX.Element {
  return (
    <SvgFrame {...props}>
      <circle cx="12" cy="13.4" r="5.1" />
      <path d="M12 3.6v6.4" />
      <path d="M9.1 7.4 12 10.3l2.9-2.9" />
    </SvgFrame>
  );
}

function CollectGlyph(props: GlyphProps): JSX.Element {
  return (
    <SvgFrame {...props}>
      <path d="M4.6 9.6h3.2L16.8 5v14.2L7.8 14.6H4.6Z" />
      <path d="M8.2 14.8c.2 2.2 1.5 3.6 3.4 3.6" />
    </SvgFrame>
  );
}

function CashGlyph(props: GlyphProps): JSX.Element {
  return (
    <SvgFrame {...props}>
      <path d="M12 3.8v3.2" />
      <path d="M5.4 7.6h13.2" />
      <path d="M5.4 7.6 3.2 14h4.4Z" />
      <path d="M18.6 7.6 20.8 14h-4.4Z" />
      <path d="M12 7.4V20.2" />
    </SvgFrame>
  );
}

function CloseGlyph(props: GlyphProps): JSX.Element {
  return (
    <SvgFrame {...props}>
      <rect x="4.2" y="5.8" width="15.6" height="14.2" rx="1.5" />
      <path d="M4.2 10.2h15.6" />
      <path d="M8 4.2v3.6M16 4.2v3.6" />
      <path d="M8.6 15.2 11 17.5l4.6-4.8" />
    </SvgFrame>
  );
}

function StoryGlyph(props: GlyphProps): JSX.Element {
  return (
    <SvgFrame {...props}>
      <path d="M4.2 19V5.4" />
      <path d="M4.2 19h15.6" />
      <path d="M6.4 14.6 10.2 10l3.2 2.4 4.6-6.2" />
    </SvgFrame>
  );
}

function Shield({ children, ...props }: GlyphProps & { children: ReactNode }): JSX.Element {
  return (
    <SvgFrame {...props}>
      <path d="M12 3.2 19.6 6v5.4c0 4.8-3.2 7.8-7.6 8.8C7.6 19.2 4.4 16.2 4.4 11.4V6Z" />
      {children}
    </SvgFrame>
  );
}

function CtlPayGlyph(props: GlyphProps): JSX.Element {
  return (
    <Shield {...props}>
      <path d="M9 12.1 11 14.1l4.1-4.3" />
    </Shield>
  );
}

function CtlCashGlyph(props: GlyphProps): JSX.Element {
  return (
    <Shield {...props}>
      <circle cx="12" cy="12.1" r="2.7" />
    </Shield>
  );
}

function CtlBooksGlyph(props: GlyphProps): JSX.Element {
  return (
    <Shield {...props}>
      <path d="M8.4 11h7.2M8.4 14h7.2" />
    </Shield>
  );
}

function AuditGlyph(props: GlyphProps): JSX.Element {
  return (
    <SvgFrame {...props}>
      <circle cx="10.4" cy="10.4" r="5.4" />
      <path d="M14.6 14.6 20 20" />
    </SvgFrame>
  );
}

function WorldGlyph(props: GlyphProps): JSX.Element {
  return (
    <SvgFrame {...props}>
      <circle cx="12" cy="12" r="8" />
      <path d="M4 12h16" />
      <path d="M12 4c2.6 2.6 2.6 13.4 0 16M12 4c-2.6 2.6-2.6 13.4 0 16" />
      <path d="M5.6 8.2c4 1.2 8.8 1.2 12.8 0M5.6 15.8c4-1.2 8.8-1.2 12.8 0" />
    </SvgFrame>
  );
}

function EventGlyph(props: GlyphProps): JSX.Element {
  return (
    <SvgFrame {...props}>
      <path d="M7 3.6h7.2L18.8 8v12.4H7Z" />
      <path d="M14.2 3.6V8h4.6" />
      <path d="M9.4 12.2h6.2M9.4 15.4h6.2" />
    </SvgFrame>
  );
}

function FallbackGlyph(props: GlyphProps): JSX.Element {
  return (
    <SvgFrame {...props}>
      <path d="M12 3.4 20.2 8v8L12 20.6 3.8 16V8Z" />
    </SvgFrame>
  );
}

const GLYPHS: Record<IconSlug, (props: GlyphProps) => JSX.Element> = {
  email: EmailGlyph,
  stripe: StripeGlyph,
  bank: BankGlyph,
  books: BooksGlyph,
  ap: ApGlyph,
  pay: PayGlyph,
  apply: ApplyGlyph,
  collect: CollectGlyph,
  cash: CashGlyph,
  close: CloseGlyph,
  story: StoryGlyph,
  "ctl-pay": CtlPayGlyph,
  "ctl-cash": CtlCashGlyph,
  "ctl-books": CtlBooksGlyph,
  audit: AuditGlyph,
  world: WorldGlyph,
  event: EventGlyph,
};

export function isIconSlug(value: string): value is IconSlug {
  return Object.prototype.hasOwnProperty.call(GLYPHS, value);
}

export function AgentIcon({ slug, size = 22, className }: AgentIconProps): JSX.Element {
  const Glyph = isIconSlug(slug) ? GLYPHS[slug] : FallbackGlyph;
  return <Glyph size={size} className={className} />;
}
