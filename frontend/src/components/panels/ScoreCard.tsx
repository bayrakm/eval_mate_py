"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Eye, Hash } from "lucide-react";
import type { EvalScoreItem, RubricItem } from "@/lib/types";
import { formatScore } from "@/lib/format";

interface ScoreCardProps {
  item: EvalScoreItem;
  rubricItem?: RubricItem;
}

export function ScoreCard({ item, rubricItem }: ScoreCardProps) {
  return (
    <Card className="w-full">
      <CardHeader className="pb-3">
        <CardTitle className="text-lg flex items-center justify-between">
          <span>{rubricItem?.title || `Item ${item.rubric_item_id.slice(0, 8)}`}</span>
          <div className="text-right">
            <div className="text-2xl font-bold text-primary">
              {formatScore(item.score)}
            </div>
            {rubricItem?.weight && (
              <div className="text-sm text-muted-foreground">
                Weight: {(rubricItem.weight * 100).toFixed(0)}%
              </div>
            )}
          </div>
        </CardTitle>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Score Progress Bar */}
        <div>
          <div className="flex justify-between text-sm mb-2">
            <span>Score</span>
            <span>{item.score}/100</span>
          </div>
          <Progress value={item.score} className="h-2" />
        </div>

        {/* Criterion */}
        {rubricItem?.criterion && (
          <div>
            <div className="text-sm font-medium mb-1">Criterion</div>
            <Badge variant="secondary">{rubricItem.criterion}</Badge>
          </div>
        )}

        {/* Description */}
        {rubricItem?.description && (
          <div>
            <div className="text-sm font-medium mb-2">Description</div>
            <p className="text-sm text-muted-foreground">{rubricItem.description}</p>
          </div>
        )}

        {/* Justification */}
        <div>
          <div className="text-sm font-medium mb-2">Justification</div>
          <div className="p-3 rounded-lg bg-muted/50 border">
            <p className="text-sm whitespace-pre-wrap">{item.justification}</p>
          </div>
        </div>

        {/* Evidence Block IDs */}
        {item.evidence_block_ids.length > 0 && (
          <div>
            <div className="text-sm font-medium mb-2 flex items-center gap-2">
              <Eye className="w-4 h-4" />
              Evidence References
            </div>
            <div className="flex flex-wrap gap-2">
              {item.evidence_block_ids.map((blockId, index) => (
                <Badge key={index} variant="outline" className="text-xs">
                  <Hash className="w-3 h-3 mr-1" />
                  {blockId.slice(0, 8)}...
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Rubric Item ID */}
        <div className="pt-2 border-t">
          <div className="text-xs text-muted-foreground">
            Rubric Item: {item.rubric_item_id}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Simple Badge component since we need it
interface BadgeProps {
  children: React.ReactNode;
  variant?: "default" | "secondary" | "outline";
  className?: string;
}

function Badge({ children, variant = "default", className = "" }: BadgeProps) {
  const baseClasses = "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2";
  
  const variantClasses = {
    default: "border-transparent bg-primary text-primary-foreground hover:bg-primary/80",
    secondary: "border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80",
    outline: "border-border text-foreground",
  };

  return (
    <div className={`${baseClasses} ${variantClasses[variant]} ${className}`}>
      {children}
    </div>
  );
}

// Simple Progress component since we need it
interface ProgressProps {
  value: number;
  className?: string;
}

function Progress({ value, className = "" }: ProgressProps) {
  return (
    <div className={`relative h-4 w-full overflow-hidden rounded-full bg-secondary ${className}`}>
      <div
        className="h-full w-full flex-1 bg-primary transition-all"
        style={{ transform: `translateX(-${100 - Math.max(0, Math.min(100, value))}%)` }}
      />
    </div>
  );
}