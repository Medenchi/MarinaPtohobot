import { useEffect, useState } from "react";
import { Plus, Copy } from "@phosphor-icons/react";
import { getSupabase } from "@/lib/supabase";

type Post = {
  id: string;
  code: string;
  created_at: string;
  clicks: number;
};

export default function Posts() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const client = getSupabase("mama");

  async function load() {
    setLoading(true);
    const { data } = await client
      .from("posts")
      .select("*")
      .order("created_at", { ascending: false });
    if (data) setPosts(data);
    setLoading(false);
  }

  useEffect(() => {
    load();
  }, []);

  async function createPost() {
    // Generate 9 character random string
    const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
    let code = "";
    for (let i = 0; i < 9; i++) {
      code += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    await client.from("posts").insert([{ code }]);
    load();
  }

  function copyLink(code: string) {
    const link = `https://t.me/MarinaPtohobot?start=${code}`;
    navigator.clipboard.writeText(link);
    alert("Ссылка скопирована: " + link);
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="serif-heading text-2xl">Посты (Deep Links)</h1>
        <button
          onClick={createPost}
          className="flex items-center gap-2 bg-ink text-white px-4 py-2 text-sm uppercase tracking-tighter"
        >
          <Plus size={16} />
          Новый пост
        </button>
      </div>

      <div className="bg-white border border-line p-4 space-y-4">
        {loading ? (
          <p className="text-muted text-sm">Загрузка...</p>
        ) : posts.length === 0 ? (
          <p className="text-muted text-sm">Пока нет постов. Создайте первый!</p>
        ) : (
          <div className="space-y-4">
            {posts.map((post) => (
              <div key={post.id} className="flex items-center justify-between border-b border-line pb-4 last:border-0 last:pb-0">
                <div>
                  <p className="font-mono text-sm">{post.code}</p>
                  <p className="text-xs text-muted">Создан: {new Date(post.created_at).toLocaleString("ru-RU")}</p>
                </div>
                <div className="flex items-center gap-6">
                  <div className="text-right">
                    <p className="text-xs text-muted uppercase tracking-tighter">Переходов</p>
                    <p className="text-xl font-medium">{post.clicks}</p>
                  </div>
                  <button
                    onClick={() => copyLink(post.code)}
                    className="flex items-center gap-1 text-xs text-muted hover:text-ink transition-colors"
                  >
                    <Copy size={16} /> Копировать ссылку
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
