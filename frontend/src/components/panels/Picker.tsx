"use client";

import { useState, useEffect } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { FileText, HelpCircle, User, Check } from "lucide-react";
import type { 
  RubricMeta, 
  QuestionMeta, 
  SubmissionMeta, 
  Rubric, 
  Question, 
  Submission 
} from "@/lib/types";

interface PickerProps {
  selectedRubric: Rubric | null;
  selectedQuestion: Question | null;
  selectedSubmission: Submission | null;
  onRubricSelect: (rubric: Rubric) => void;
  onQuestionSelect: (question: Question) => void;
  onSubmissionSelect: (submission: Submission) => void;
  onLoadRubrics: () => Promise<RubricMeta[]>;
  onLoadQuestions: (rubricId: string) => Promise<QuestionMeta[]>;
  onLoadSubmissions: (filters?: { rubric_id?: string; question_id?: string; student_handle?: string; }) => Promise<SubmissionMeta[]>;
  onGetRubric: (id: string) => Promise<Rubric>;
  onGetQuestion: (id: string) => Promise<Question>;
  onGetSubmission: (id: string) => Promise<Submission>;
}

export function Picker({
  selectedRubric,
  selectedQuestion,
  selectedSubmission,
  onRubricSelect,
  onQuestionSelect,
  onSubmissionSelect,
  onLoadRubrics,
  onLoadQuestions,
  onLoadSubmissions,
  onGetRubric,
  onGetQuestion,
  onGetSubmission,
}: PickerProps) {
  const [activeTab, setActiveTab] = useState<"rubrics" | "questions" | "submissions">("rubrics");
  const [rubrics, setRubrics] = useState<RubricMeta[]>([]);
  const [questions, setQuestions] = useState<QuestionMeta[]>([]);
  const [submissions, setSubmissions] = useState<SubmissionMeta[]>([]);
  const [loading, setLoading] = useState<string>("");

  // Load rubrics on mount
  useEffect(() => {
    loadRubrics();
  }, []);

  // Load questions when rubric is selected
  useEffect(() => {
    if (selectedRubric) {
      loadQuestions();
    } else {
      setQuestions([]);
    }
  }, [selectedRubric]);

  // Load submissions when both rubric and question are selected
  useEffect(() => {
    if (selectedRubric && selectedQuestion) {
      loadSubmissions();
    } else {
      setSubmissions([]);
    }
  }, [selectedRubric, selectedQuestion]);

  const loadRubrics = async () => {
    try {
      setLoading("rubrics");
      const data = await onLoadRubrics();
      setRubrics(data);
    } catch (error) {
      console.error("Failed to load rubrics:", error);
    } finally {
      setLoading("");
    }
  };

  const loadQuestions = async () => {
    if (!selectedRubric) return;
    try {
      setLoading("questions");
      const data = await onLoadQuestions(selectedRubric.id);
      setQuestions(data);
    } catch (error) {
      console.error("Failed to load questions:", error);
    } finally {
      setLoading("");
    }
  };

  const loadSubmissions = async () => {
    if (!selectedRubric || !selectedQuestion) return;
    try {
      setLoading("submissions");
      const data = await onLoadSubmissions({ rubric_id: selectedRubric.id, question_id: selectedQuestion.id });
      setSubmissions(data);
    } catch (error) {
      console.error("Failed to load submissions:", error);
    } finally {
      setLoading("");
    }
  };

  const handleRubricSelect = async (rubricMeta: RubricMeta) => {
    try {
      setLoading(`rubric-${rubricMeta.id}`);
      const rubric = await onGetRubric(rubricMeta.id);
      onRubricSelect(rubric);
    } catch (error) {
      console.error("Failed to load rubric:", error);
    } finally {
      setLoading("");
    }
  };

  const handleQuestionSelect = async (questionMeta: QuestionMeta) => {
    try {
      setLoading(`question-${questionMeta.id}`);
      const question = await onGetQuestion(questionMeta.id);
      onQuestionSelect(question);
    } catch (error) {
      console.error("Failed to load question:", error);
    } finally {
      setLoading("");
    }
  };

  const handleSubmissionSelect = async (submissionMeta: SubmissionMeta) => {
    try {
      setLoading(`submission-${submissionMeta.id}`);
      const submission = await onGetSubmission(submissionMeta.id);
      onSubmissionSelect(submission);
    } catch (error) {
      console.error("Failed to load submission:", error);
    } finally {
      setLoading("");
    }
  };

  const tabs = [
    { id: "rubrics", label: "Rubrics", icon: FileText },
    { id: "questions", label: "Questions", icon: HelpCircle },
    { id: "submissions", label: "Submissions", icon: User },
  ] as const;

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Select Resources</CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        {/* Tab Navigation */}
        <div className="border-b">
          <div className="flex">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              const isDisabled = 
                (tab.id === "questions" && !selectedRubric) ||
                (tab.id === "submissions" && (!selectedRubric || !selectedQuestion));
              
              return (
                <button
                  key={tab.id}
                  onClick={() => !isDisabled && setActiveTab(tab.id)}
                  disabled={isDisabled}
                  className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors border-b-2 ${
                    isActive
                      ? "border-primary text-primary"
                      : isDisabled
                      ? "border-transparent text-muted-foreground opacity-50 cursor-not-allowed"
                      : "border-transparent text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {tab.label}
                  {/* Show checkmark if item is selected */}
                  {((tab.id === "rubrics" && selectedRubric) ||
                    (tab.id === "questions" && selectedQuestion) ||
                    (tab.id === "submissions" && selectedSubmission)) && (
                    <Check className="w-4 h-4 text-green-500" />
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Tab Content */}
        <div className="p-4 h-96 overflow-y-auto">
          {/* Rubrics Tab */}
          {activeTab === "rubrics" && (
            <div className="space-y-2">
              {loading === "rubrics" ? (
                <div className="flex items-center justify-center py-8">
                  <Spinner />
                </div>
              ) : rubrics.length === 0 ? (
                <p className="text-muted-foreground text-center py-8">
                  No rubrics found. Upload one to get started.
                </p>
              ) : (
                rubrics.map((rubric) => (
                  <div
                    key={rubric.id}
                    className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                      selectedRubric?.id === rubric.id
                        ? "border-primary bg-primary/5"
                        : "border-border hover:border-primary/50"
                    }`}
                    onClick={() => handleRubricSelect(rubric)}
                  >
                    {loading === `rubric-${rubric.id}` ? (
                      <div className="flex items-center gap-2">
                        <Spinner size="sm" />
                        <span>Loading...</span>
                      </div>
                    ) : (
                      <div>
                        <div className="font-medium">{rubric.assignment}</div>
                        <div className="text-sm text-muted-foreground">
                          {rubric.course} • v{rubric.version}
                        </div>
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          )}

          {/* Questions Tab */}
          {activeTab === "questions" && (
            <div className="space-y-2">
              {loading === "questions" ? (
                <div className="flex items-center justify-center py-8">
                  <Spinner />
                </div>
              ) : questions.length === 0 ? (
                <p className="text-muted-foreground text-center py-8">
                  {selectedRubric 
                    ? "No questions found for this rubric. Upload one to continue."
                    : "Select a rubric first."
                  }
                </p>
              ) : (
                questions.map((question) => (
                  <div
                    key={question.id}
                    className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                      selectedQuestion?.id === question.id
                        ? "border-primary bg-primary/5"
                        : "border-border hover:border-primary/50"
                    }`}
                    onClick={() => handleQuestionSelect(question)}
                  >
                    {loading === `question-${question.id}` ? (
                      <div className="flex items-center gap-2">
                        <Spinner size="sm" />
                        <span>Loading...</span>
                      </div>
                    ) : (
                      <div>
                        <div className="font-medium">{question.title}</div>
                        <div className="text-sm text-muted-foreground">
                          ID: {question.id.slice(0, 8)}...
                        </div>
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          )}

          {/* Submissions Tab */}
          {activeTab === "submissions" && (
            <div className="space-y-2">
              {loading === "submissions" ? (
                <div className="flex items-center justify-center py-8">
                  <Spinner />
                </div>
              ) : submissions.length === 0 ? (
                <p className="text-muted-foreground text-center py-8">
                  {selectedRubric && selectedQuestion
                    ? "No submissions found. Upload one to continue."
                    : "Select a rubric and question first."
                  }
                </p>
              ) : (
                submissions.map((submission) => (
                  <div
                    key={submission.id}
                    className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                      selectedSubmission?.id === submission.id
                        ? "border-primary bg-primary/5"
                        : "border-border hover:border-primary/50"
                    }`}
                    onClick={() => handleSubmissionSelect(submission)}
                  >
                    {loading === `submission-${submission.id}` ? (
                      <div className="flex items-center gap-2">
                        <Spinner size="sm" />
                        <span>Loading...</span>
                      </div>
                    ) : (
                      <div>
                        <div className="font-medium">{submission.student_handle}</div>
                        <div className="text-sm text-muted-foreground">
                          ID: {submission.id.slice(0, 8)}...
                        </div>
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}