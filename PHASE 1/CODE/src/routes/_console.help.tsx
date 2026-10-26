import { createFileRoute } from "@tanstack/react-router";
import { BookOpen, LifeBuoy, Mail, MessageSquare } from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/page-header";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

export const Route = createFileRoute("/_console/help")({
  head: () => ({
    meta: [
      { title: "Help & Support — AquaSense" },
      { name: "description", content: "Documentation, FAQs and support contact for the AI-based acoustic water leak detection system." },
      { property: "og:title", content: "Help & Support — AquaSense" },
      { property: "og:description", content: "Guides and support for AquaSense operators." },
    ],
  }),
  component: HelpPage,
});

const faqs = [
  {
    q: "How does acoustic leak detection work?",
    a: "Each node continuously samples pipe-borne sound. A trained classifier compares the live spectrum against the node's learned baseline; sustained energy in the 700–1500 Hz band with high confidence is flagged as a leak signature.",
  },
  {
    q: "What does the 55 dB threshold mean?",
    a: "It is the alert trigger level above the ambient noise floor. Any sustained reading above it raises an event, which the classifier then scores for severity and estimated water loss.",
  },
  {
    q: "Why is a device shown as offline?",
    a: "A node is marked offline when it has not reported for over an hour — usually low battery or poor network coverage. Check the fleet health panel on the dashboard for battery and signal levels.",
  },
  {
    q: "How are reports generated?",
    a: "Reports aggregate leak events, water loss and sensor health for the selected period and can be exported as PDF for review or Excel for further analysis.",
  },
];

function HelpPage() {
  return (
    <div className="space-y-6">
      <PageHeader title="Help & support" description="Guides, FAQs and a direct line to the project team." />

      <div className="grid gap-4 sm:grid-cols-3">
        {[
          { icon: BookOpen, title: "Documentation", text: "System architecture, sensor setup and model details." },
          { icon: LifeBuoy, title: "Field guide", text: "Step-by-step leak verification and repair workflow." },
          { icon: MessageSquare, title: "Community", text: "Discuss deployments with other operators." },
        ].map((c) => (
          <Card key={c.title} className="card-hover border-border/70">
            <CardContent className="space-y-2 p-6">
              <span className="grid size-10 place-items-center rounded-xl bg-primary/10 text-primary">
                <c.icon className="size-5" />
              </span>
              <p className="font-display font-semibold">{c.title}</p>
              <p className="text-sm text-muted-foreground">{c.text}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card className="border-border/70">
          <CardHeader>
            <CardTitle className="font-display text-lg">Frequently asked questions</CardTitle>
            <CardDescription>The essentials for demo day and daily operations</CardDescription>
          </CardHeader>
          <CardContent>
            <Accordion type="single" collapsible className="w-full">
              {faqs.map((f, i) => (
                <AccordionItem key={f.q} value={`item-${i}`}>
                  <AccordionTrigger className="text-left">{f.q}</AccordionTrigger>
                  <AccordionContent className="text-muted-foreground">{f.a}</AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          </CardContent>
        </Card>

        <Card className="border-border/70">
          <CardHeader>
            <CardTitle className="font-display text-lg">Contact support</CardTitle>
            <CardDescription>We reply within one working day</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="hsubject">Subject</Label>
              <Input id="hsubject" placeholder="Sensor ACD-06 not reporting" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="hmsg">Message</Label>
              <Textarea id="hmsg" rows={5} placeholder="Describe the issue and the affected zone…" />
            </div>
            <Button onClick={() => toast.success("Support request sent")}>
              <Mail className="mr-2 size-4" /> Send request
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
