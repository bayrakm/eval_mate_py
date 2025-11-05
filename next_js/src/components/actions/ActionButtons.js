"use client";

import { Group, Button } from "@mantine/core";
import { IconFileUpload, IconArrowRight } from "@tabler/icons-react";
import { LOADING_STATES } from "../../lib/constants";

export function ActionButtons({
  onBuildFusion,
  onEvaluate,
  canBuildFusion,
  canEvaluate,
  loading,
}) {
  const isBuilding = loading === LOADING_STATES.BUILDING;
  const isEvaluating = loading === LOADING_STATES.EVALUATING;

  const isBuildFusionDisabled = !canBuildFusion || isBuilding || isEvaluating;
  const isEvaluateDisabled = !canEvaluate || isBuilding || isEvaluating;

  return (
    <Group justify="center" gap="md">
      <Button
        variant="light"
        leftSection={<IconFileUpload size={18} />}
        onClick={onBuildFusion}
        disabled={isBuildFusionDisabled}
        loading={isBuilding}
        size="lg"
      >
        Build Fusion
      </Button>

      <Button
        leftSection={<IconArrowRight size={18} />}
        onClick={onEvaluate}
        disabled={isEvaluateDisabled}
        loading={isEvaluating}
        color="orange"
        size="lg"
      >
        Run Evaluation
      </Button>
    </Group>
  );
}
