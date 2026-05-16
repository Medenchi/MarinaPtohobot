import { Camera, Sparkle, BookOpen } from "@phosphor-icons/react";

export default function Landing() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-6 text-center">
      <h1 className="serif-heading text-4xl md:text-5xl mb-4">
        Marina Photo
      </h1>
      <p className="text-muted max-w-md mb-10 text-sm leading-relaxed">
        Подбор образов для фотосессии и бесплатные материалы от фотографа Марины
        Заугольниковой.
      </p>

      <div className="flex flex-col gap-3 w-full max-w-xs">
        <a
          href="https://zaugolnikova.ru/"
          target="_blank"
          rel="noopener noreferrer"
          className="btn-primary"
        >
          <Camera size={18} weight="bold" />
          Заказать съёмку
        </a>

        <a href="/app" className="btn-outline">
          <Sparkle size={18} weight="bold" />
          Подобрать образ
        </a>

        <a href="/reader" className="btn-outline">
          <BookOpen size={18} weight="bold" />
          Материалы
        </a>
      </div>

      <footer className="footer-brand mt-16">
        <a
          href="https://malinacode.is-a.dev"
          target="_blank"
          rel="noopener noreferrer"
        >
          malinacode
        </a>
      </footer>
    </div>
  );
}
