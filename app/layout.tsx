import type { Metadata } from 'next';
import './globals.css';
export const metadata:Metadata={metadataBase:new URL(process.env.NEXT_PUBLIC_SITE_URL||'http://localhost:3000'),title:'恵美子新聞｜煽られずに、世の中を知る。',description:'重要なことだけを、落ち着いた日本語で短時間に読める個人用ニュースサイト。',openGraph:{title:'恵美子新聞',description:'煽られずに、世の中を知る。',type:'website',images:['/og.png']},twitter:{card:'summary_large_image',title:'恵美子新聞',description:'煽られずに、世の中を知る。',images:['/og.png']}};
export default function RootLayout({children}:Readonly<{children:React.ReactNode}>){return <html lang="ja"><body>{children}</body></html>}
