import Image from "next/image";
import Link from "next/link";

type ImageLinkCardProps = {
  href: string;
  image: string;
  title: string;
  description?: string;
  eyebrow?: string;
  tall?: boolean;
};

export function ImageLinkCard({
  href,
  image,
  title,
  description,
  eyebrow,
  tall = false,
}: ImageLinkCardProps) {
  return (
    <Link
      href={href}
      className="group block rounded-2xl focus:outline-none focus:ring-2 focus:ring-accent-500"
    >
      <article
        className={`image-link-card relative overflow-hidden rounded-2xl border border-border shadow-sm ${
          tall ? "flex h-[350px] flex-col justify-end" : ""
        }`}
      >
        <Image
          src={image}
          alt=""
          fill
          className="object-cover"
          sizes="(max-width: 768px) 100vw, 33vw"
        />
        <div
          className="absolute inset-0 bg-gradient-to-b from-slate-950/20 to-slate-950/75 transition group-hover:from-slate-950/30 group-hover:to-slate-950/80"
          aria-hidden="true"
        />
        <div
          className={`relative p-6 ${
            tall
              ? "origin-bottom transition-transform duration-300 ease-in-out group-hover:scale-y-105"
              : ""
          }`}
        >
          {eyebrow ? (
            <p className="text-4xl font-bold text-white">{eyebrow}</p>
          ) : null}
          <h3
            className={`text-lg font-semibold text-white ${eyebrow ? "mt-3 text-xl text-slate-100" : "underline"}`}
          >
            {title}
          </h3>
          {description ? (
            <p className={`mt-2 ${eyebrow ? "text-slate-100" : "text-slate-100"}`}>
              {description}
            </p>
          ) : null}
        </div>
      </article>
    </Link>
  );
}
