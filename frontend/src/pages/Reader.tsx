import { useEffect, useState, useRef, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import { DownloadSimple, CaretLeft, CaretRight } from "@phosphor-icons/react";
import * as pdfjsLib from "pdfjs-dist";
import Spinner from "@/components/Spinner";
import Footer from "@/components/Footer";

pdfjsLib.GlobalWorkerOptions.workerSrc = `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.mjs`;

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL || "";
const BUCKET = "course-files";

export default function Reader() {
  const [params] = useSearchParams();
  const courseId = params.get("course");
  const fileId = params.get("file");

  const canvasRef = useRef<HTMLCanvasElement>(null);

  const [loading, setLoading] = useState(true);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [fileName, setFileName] = useState("");
  const [pageNum, setPageNum] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [pdfDoc, setPdfDoc] = useState<pdfjsLib.PDFDocumentProxy | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!courseId || !fileId) {
      setError("Не указан файл");
      setLoading(false);
      return;
    }

    (async () => {
      try {
        const { supabase } = await import("@/lib/supabase");
        const { data: fileRow } = await supabase
          .from("course_files")
          .select("title, storage_path, mime_type")
          .eq("id", Number(fileId))
          .single();

        if (!fileRow) {
          setError("Файл не найден");
          setLoading(false);
          return;
        }

        setFileName(fileRow.title);
        const url = `${SUPABASE_URL}/storage/v1/object/public/${BUCKET}/${fileRow.storage_path}`;
        setPdfUrl(url);

        const doc = await pdfjsLib.getDocument(url).promise;
        setPdfDoc(doc);
        setTotalPages(doc.numPages);
        setPageNum(1);
      } catch {
        setError("Не удалось загрузить PDF");
      } finally {
        setLoading(false);
      }
    })();
  }, [courseId, fileId]);

  const renderPage = useCallback(
    async (num: number) => {
      if (!pdfDoc || !canvasRef.current) return;
      const page = await pdfDoc.getPage(num);
      const scale = Math.min(
        (window.innerWidth - 32) / page.getViewport({ scale: 1 }).width,
        2.0,
      );
      const viewport = page.getViewport({ scale });
      const canvas = canvasRef.current;
      canvas.width = viewport.width;
      canvas.height = viewport.height;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      await page.render({ canvasContext: ctx, viewport }).promise;
    },
    [pdfDoc],
  );

  useEffect(() => {
    void renderPage(pageNum);
  }, [pageNum, renderPage]);

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col">
        <Spinner label="Загрузка PDF..." />
        <Footer />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center">
        <p className="text-muted">{error}</p>
        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-white">
      <header className="sticky top-0 z-10 flex items-center justify-between border-b border-line bg-paper/90 backdrop-blur px-4 py-3">
        <span className="text-sm font-medium truncate max-w-[60%]">
          {fileName}
        </span>
        {pdfUrl && (
          <a
            href={pdfUrl}
            download
            className="btn-outline !px-3 !py-1.5 text-xs"
          >
            <DownloadSimple size={14} weight="bold" />
            Скачать
          </a>
        )}
      </header>

      <div className="flex-1 flex items-start justify-center overflow-auto p-4">
        <canvas ref={canvasRef} className="max-w-full shadow-md" />
      </div>

      {totalPages > 1 && (
        <nav className="sticky bottom-0 flex items-center justify-center gap-6 border-t border-line bg-paper/90 backdrop-blur px-4 py-3">
          <button
            disabled={pageNum <= 1}
            onClick={() => setPageNum((n) => Math.max(1, n - 1))}
            className="btn-outline !px-3 !py-1.5 disabled:opacity-30"
          >
            <CaretLeft size={16} weight="bold" />
          </button>
          <span className="text-sm text-muted tabular-nums">
            {pageNum} / {totalPages}
          </span>
          <button
            disabled={pageNum >= totalPages}
            onClick={() => setPageNum((n) => Math.min(totalPages, n + 1))}
            className="btn-outline !px-3 !py-1.5 disabled:opacity-30"
          >
            <CaretRight size={16} weight="bold" />
          </button>
        </nav>
      )}

      <Footer />
    </div>
  );
}
