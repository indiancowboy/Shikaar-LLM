// Branding: the Shikaar wordmark and the Two Brown Guys Hunt credit.

// Social links. An empty link hides its icon.
export const TBGH_LINKS = {
  website: "https://twobrownguyshunt.com",
  youtube: "",
  instagram: "",
};

export function ShikaarLogo({ className }: { className?: string }) {
  // 640×401 source; width/height reserve space so the page doesn't jump.
  return <img src="/shikaar-logo.png" alt="Shikaar" width={640} height={401} className={className} />;
}

function YouTubeIcon() {
  return (
    <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true">
      <path
        fill="currentColor"
        d="M23.5 6.2a3 3 0 0 0-2.1-2.1C19.5 3.6 12 3.6 12 3.6s-7.5 0-9.4.5A3 3 0 0 0 .5 6.2 31 31 0 0 0 0 12a31 31 0 0 0 .5 5.8 3 3 0 0 0 2.1 2.1c1.9.5 9.4.5 9.4.5s7.5 0 9.4-.5a3 3 0 0 0 2.1-2.1A31 31 0 0 0 24 12a31 31 0 0 0-.5-5.8zM9.6 15.6V8.4l6.2 3.6-6.2 3.6z"
      />
    </svg>
  );
}

function InstagramIcon() {
  return (
    <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
      <rect x="3" y="3" width="18" height="18" rx="5" />
      <circle cx="12" cy="12" r="4" />
      <circle cx="17.5" cy="6.5" r="1.2" fill="currentColor" stroke="none" />
    </svg>
  );
}

/** "A Two Brown Guys Hunt app" — badge links to the website, socials below. */
export function TbghCredit({ size = 96 }: { size?: number }) {
  const ext = { target: "_blank", rel: "noopener noreferrer" } as const;
  return (
    <div className="tbgh">
      <a href={TBGH_LINKS.website} {...ext} aria-label="Two Brown Guys Hunt website">
        <img src="/tbgh-badge.png" alt="Two Brown Guys Hunt" width={size} height={Math.round(size * 0.973)} />
      </a>
      <div className="tbgh-by">A Two Brown Guys Hunt app</div>
      {TBGH_LINKS.youtube || TBGH_LINKS.instagram ? (
        <div className="tbgh-social">
          {TBGH_LINKS.youtube ? (
            <a href={TBGH_LINKS.youtube} {...ext} aria-label="YouTube">
              <YouTubeIcon />
            </a>
          ) : null}
          {TBGH_LINKS.instagram ? (
            <a href={TBGH_LINKS.instagram} {...ext} aria-label="Instagram">
              <InstagramIcon />
            </a>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
