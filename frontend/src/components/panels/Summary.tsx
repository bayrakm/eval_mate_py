"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Download, FileText, BarChart } from "lucide-react";
import type { FusionContext, EvalResult } from "@/lib/types";
import { formatTokens, formatScore, downloadJSON, downloadCSV } from "@/lib/format";

interface SummaryProps {
  fusion: FusionContext | null;
  result: EvalResult | null;
  onDownloadJSON?: () => void;
  onDownloadCSV?: () => void;
}

export function Summary({ fusion, result, onDownloadJSON, onDownloadCSV }: SummaryProps) {
  if (!fusion && !result) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-center py-8">
            Build fusion context to see summary
          </p>
        </CardContent>
      </Card>
    );
  }

  const handleDownloadJSON = () => {
    if (result) {
      downloadJSON(result, `evaluation-${result.submission_id}.json`);
    }
    onDownloadJSON?.();
  };

  const handleDownloadCSV = () => {
    if (result) {
      downloadCSV(result, `evaluation-${result.submission_id}.csv`);
    }
    onDownloadCSV?.();
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BarChart className="w-5 h-5" />
          Summary
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Fusion Context Summary */}
        {fusion && (
          <div className="space-y-4">
            <h3 className="font-semibold text-sm uppercase tracking-wide text-muted-foreground">
              Fusion Context
            </h3>
            
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <div className="font-medium">Token Estimate</div>
                <div className="text-muted-foreground">{formatTokens(fusion.token_estimate)}</div>
              </div>
              <div>
                <div className="font-medium">Visual Count</div>
                <div className="text-muted-foreground">{fusion.visual_count} items</div>
              </div>
              <div>
                <div className="font-medium">Text Blocks</div>
                <div className="text-muted-foreground">{fusion.text_block_count} blocks</div>
              </div>
              <div>
                <div className="font-medium">Rubric Items</div>
                <div className="text-muted-foreground">{fusion.rubric_items.length} items</div>
              </div>
            </div>

            <div className="pt-2 border-t">
              <div className="font-medium text-sm mb-2">Question Preview</div>
              <p className="text-sm text-muted-foreground line-clamp-3">
                {fusion.question_text.slice(0, 200)}
                {fusion.question_text.length > 200 && "..."}
              </p>
            </div>

            <div className="pt-2 border-t">
              <div className="font-medium text-sm mb-2">Submission Preview</div>
              <p className="text-sm text-muted-foreground line-clamp-3">
                {fusion.submission_text.slice(0, 200)}
                {fusion.submission_text.length > 200 && "..."}
              </p>
            </div>
          </div>
        )}

        {/* Evaluation Results Summary */}
        {result && (
          <div className="space-y-4">
            <h3 className="font-semibold text-sm uppercase tracking-wide text-muted-foreground">
              Evaluation Results
            </h3>
            
            <div className="space-y-3">
              {/* Total Score */}
              <div className="p-4 rounded-lg bg-primary/5 border border-primary/20">
                <div className="text-center">
                  <div className="text-2xl font-bold text-primary">
                    {formatScore(result.total)}
                  </div>
                  <div className="text-sm text-muted-foreground">Total Score</div>
                </div>
              </div>

              {/* Score Breakdown */}
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <div className="font-medium">Items Graded</div>
                  <div className="text-muted-foreground">{result.items.length} items</div>
                </div>
                <div>
                  <div className="font-medium">Average Score</div>
                  <div className="text-muted-foreground">
                    {formatScore(result.items.reduce((sum, item) => sum + item.score, 0) / result.items.length)}
                  </div>
                </div>
              </div>

              {/* Overall Feedback Preview */}
              {result.overall_feedback && (
                <div className="pt-2 border-t">
                  <div className="font-medium text-sm mb-2">Overall Feedback</div>
                  <p className="text-sm text-muted-foreground line-clamp-4">
                    {result.overall_feedback}
                  </p>
                </div>
              )}

              {/* Download Buttons */}
              <div className="pt-4 border-t space-y-2">
                <div className="font-medium text-sm mb-3">Export Results</div>
                <div className="flex gap-2">
                  <Button
                    onClick={handleDownloadJSON}
                    variant="outline"
                    size="sm"
                    className="flex-1"
                  >
                    <FileText className="w-4 h-4 mr-2" />
                    Download JSON
                  </Button>
                  <Button
                    onClick={handleDownloadCSV}
                    variant="outline"
                    size="sm"
                    className="flex-1"
                  >
                    <Download className="w-4 h-4 mr-2" />
                    Download CSV
                  </Button>
                </div>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}