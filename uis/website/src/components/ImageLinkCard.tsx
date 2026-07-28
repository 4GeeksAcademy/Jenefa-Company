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
    className="image-link-card relative flex h-[320px] flex-col justify-end overflow-hidden rounded-2xl border border-border shadow-sm"
  >
    <Image
      src={image}
      alt=""
      fill
      className="object-cover object-center"
      sizes="(max-width: 768px) 100vw, 33vw"
    />
    <div
      className="absolute inset-0 bg-gradient-to-b from-slate-950/20 to-slate-950/75 transition group-hover:from-slate-950/30 group-hover:to-slate-950/80"
      aria-hidden="true"
    />
    <div className="relative p-6">
      {eyebrow ? (
        <p className="text-2xl font-bold text-white">{eyebrow}</p>
      ) : null}
     <h3
  className={`
   w-[calc(100%+3rem)] -mx-6 px-6 py-3 text-xl font-semibold text-white transition-all duration-300
    group-hover:bg-slate-100 group-hover:text-slate-950 group-hover:shadow-md  
    ${eyebrow ? "mt-3 text-2xl text-slate-100" : ""}
  `}
>
        {title}
      </h3>
      {description ? (
        <p className="mt-2 text-slate-100">
          {description}
        </p>
      ) : null}
    </div>
  </article>
</Link>
  );
}
