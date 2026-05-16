import { useEffect, useState, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import { DownloadSimple, Camera } from "@phosphor-icons/react";
import { supabase } from "@/lib/supabase";
import OutfitCard from "@/components/OutfitCard";
import Spinner from "@/components/Spinner";
import Footer from "@/components/Footer";

interface QuizAnswers {
  colors: string[];
  styles: string[];
  seasons: string[];
  occasions: string[];
  body_types: string[];
  budgets: string[];
  shoot_types: string[];
}

interface OutfitImage {
  id: number;
  storage_path: string;
  caption: string | null;
}

interface Outfit {
  id: number;
  title: string;
  description: string | null;
  colors: string;
  styles: string;
  seasons: string;
  occasions: string;
  body_types: string;
  budgets: string;
  shoot_types: string;
  price_hint: string | null;
  outfit_images: OutfitImage[];
}

function tokens(raw: string): Set<string> {
  return new Set(
    raw
      .split(",")
      .map((s) => s.trim().toLowerCase())
      .filter(Boolean),
  );
}

function scoreOutfit(outfit: Outfit, answers: QuizAnswers): number {
  let score = 0;
  const dims: [string[], string][] = [
    [answers.colors, outfit.colors],
    [answers.styles, outfit.styles],
    [answers.seasons, outfit.seasons],
    [answers.occasions, outfit.occasions],
    [answers.body_types, outfit.body_types],
    [answers.budgets, outfit.budgets],
    [answers.shoot_types, outfit.shoot_types],
  ];
  for (const [userArr, outfitRaw] of dims) {
    const outfitSet = tokens(outfitRaw);
    if (outfitSet.size === 0) continue;
    const userSet = new Set(userArr.map((s) => s.toLowerCase()));
    for (const v of userSet) {
      if (outfitSet.has(v)) score++;
    }
  }
  return score;
}

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL || "";
const BUCKET = "outfit-images";
const PHOTOGRAPHER_URL = "https://zaugolnikova.ru/";

export default function OutfitApp() {
  const [params] = useSearchParams();
  const sessionId = params.get("s");

  const [loading, setLoading] = useState(true);
  const [outfits, setOutfits] = useState<Outfit[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      let answers: QuizAnswers | null = null;

      if (sessionId) {
        const { data: session } = await supabase
          .from("quiz_sessions")
          .select("answers")
          .eq("id", sessionId)
          .single();
        if (session?.answers) {
          answers = session.answers as QuizAnswers;
        }
      }

      const { data: all } = await supabase
        .from("outfits")
        .select("*, outfit_images(*)")
        .eq("is_published", true)
        .order("sort_order");

      let result = (all as Outfit[]) || [];

      if (answers && result.length > 0) {
        result = result
          .map((o) => ({ outfit: o, score: scoreOutfit(o, answers) }))
          .sort((a, b) => b.score - a.score)
          .map((x) => x.outfit);
      }

      setOutfits(result);
    } catch {
      setError("Не удалось загрузить образы");
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    void load();
  }, [load]);

  if (loading) return <Spinner label="Подбираю образы..." />;

  return (
    <div className="min-h-screen flex flex-col">
      <div className="px-4 pt-6 pb-2">
        <h1 className="serif-heading text-2xl text-center">Твои образы</h1>
        {sessionId && (
          <p className="text-center text-xs text-muted mt-1">
            Подобраны по твоим ответам
          </p>
        )}
      </div>

      {error ? (
        <p className="text-center text-red-500 py-10">{error}</p>
      ) : outfits.length === 0 ? (
        <p className="text-center text-muted py-10">
          Пока нет подходящих образов
        </p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 px-4 py-4">
          {outfits.map((o) => (
            <OutfitCard
              key={o.id}
              title={o.title}
              description={o.description}
              priceHint={o.price_hint}
              colors={o.colors}
              shootTypes={o.shoot_types}
              images={o.outfit_images}
              supabaseUrl={SUPABASE_URL}
              bucket={BUCKET}
            />
          ))}
        </div>
      )}

      <div className="sticky bottom-0 bg-paper/90 backdrop-blur border-t border-line px-4 py-3 flex flex-col gap-2">
        <a
          href={PHOTOGRAPHER_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="btn-primary w-full"
        >
          <Camera size={18} weight="bold" />
          Заказать съёмку
        </a>
        <button
          className="btn-outline w-full"
          onClick={() => alert("PDF download coming soon")}
        >
          <DownloadSimple size={18} weight="bold" />
          Скачать PDF-подборку
        </button>
      </div>

      <Footer />
    </div>
  );
}
