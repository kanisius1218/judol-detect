export type ReviewDecision = {
  commentId: string;
  action: "approve" | "reject" | "defer";
};

export const decisions: ReviewDecision[] = [];
