import { useEffect, useLayoutEffect, useRef } from "react";

import type { Genre } from "../types/discovery";

type GenreSelectorProps = {
  selected: Genre | null;
  onChange: (genre: Genre | null) => void;
};

const GENRES: { value: Genre; label: string }[] = [
  { value: "r&b", label: "R&B" },
  { value: "hip-hop", label: "Hip-Hop" },
  { value: "pop", label: "Pop" },
  { value: "rock", label: "Rock" },
  { value: "jazz", label: "Jazz" },
  { value: "afrobeats", label: "Afrobeats" },
];

function GenreSelector({ selected, onChange }: GenreSelectorProps) {
  const scrollerRef = useRef<HTMLDivElement>(null);

  useLayoutEffect(() => {
    const scroller = scrollerRef.current;
    if (!scroller) return;

    const buttons = Array.from(scroller.children) as HTMLElement[];
    if (buttons.length < 5) return;

    const scrollerLeft = scroller.getBoundingClientRect().left;
    const fourth = buttons[3].getBoundingClientRect();
    const fourPillWidth =
      fourth.right - scrollerLeft + parseFloat(getComputedStyle(scroller).paddingRight);

    const containerWidth = scroller.parentElement?.clientWidth ?? fourPillWidth;
    scroller.style.maxWidth = `${Math.min(fourPillWidth + 1, containerWidth)}px`;
  }, []);

  useEffect(() => {
    const scroller = scrollerRef.current;
    if (!scroller) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      return;
    }

    const timer = window.setTimeout(() => {
      scroller.scrollTo({
        left: scroller.scrollWidth - scroller.clientWidth,
        behavior: "smooth",
      });
    }, 2000);

    return () => window.clearTimeout(timer);
  }, []);

  return (
    <fieldset className="selector selector--wide">
      <legend className="selector__label">Genre</legend>

      <div className="genre-scroller" ref={scrollerRef}>
        {GENRES.map((genre) => {
          const isSelected = selected === genre.value;
          return (
            <button
              key={genre.value}
              type="button"
              className={`pill${isSelected ? " pill--selected" : ""}`}
              aria-pressed={isSelected}
              onClick={() =>
                onChange(isSelected ? null : genre.value)
              }
            >
              {genre.label}
            </button>
          );
        })}
      </div>
    </fieldset>
  );
}

export default GenreSelector;