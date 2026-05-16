import { Image as ImageIcon } from "@phosphor-icons/react";

interface OutfitImage {
  id: number;
  storage_path: string;
  caption: string | null;
}

interface OutfitCardProps {
  title: string;
  description: string | null;
  priceHint: string | null;
  colors: string;
  shootTypes: string;
  images: OutfitImage[];
  supabaseUrl: string;
  bucket: string;
}

export default function OutfitCard({
  title,
  description,
  priceHint,
  colors,
  shootTypes,
  images,
  supabaseUrl,
  bucket,
}: OutfitCardProps) {
  const imgUrl =
    images.length > 0
      ? `${supabaseUrl}/storage/v1/object/public/${bucket}/${images[0].storage_path}`
      : null;

  return (
    <div className="card group overflow-hidden">
      <div className="relative aspect-[3/4] w-full overflow-hidden rounded-lg bg-line">
        {imgUrl ? (
          <img
            src={imgUrl}
            alt={title}
            className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
            loading="lazy"
          />
        ) : (
          <div className="flex h-full items-center justify-center">
            <ImageIcon size={48} className="text-muted/40" />
          </div>
        )}
      </div>

      <div className="mt-3 space-y-1">
        <h3 className="serif-heading text-lg">{title}</h3>
        {description && (
          <p className="text-sm text-muted line-clamp-2">{description}</p>
        )}
        <div className="flex flex-wrap gap-2 pt-1 text-xs text-muted">
          {priceHint && <span>{priceHint}</span>}
          {colors && <span>{colors}</span>}
          {shootTypes && <span>{shootTypes}</span>}
        </div>
      </div>
    </div>
  );
}
