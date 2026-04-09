import { Navbar } from "@/components/navbar";
import { Hero } from "@/components/hero";
import { PainPoints } from "@/components/pain-points";
import { Features } from "@/components/features";
import { Flow } from "@/components/flow";
import { Pricing } from "@/components/pricing";
import { Cta } from "@/components/cta";
import { Footer } from "@/components/footer";

export default function Home() {
  return (
    <>
      <Navbar />
      <main>
        <Hero />
        <PainPoints />
        <Features />
        <Flow />
        <Pricing />
        <Cta />
      </main>
      <Footer />
    </>
  );
}
