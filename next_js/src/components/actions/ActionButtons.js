"use client";

import { Group, Button } from "@mantine/core";
import { IconArrowRight } from "@tabler/icons-react";
import { LOADING_STATES } from "../../lib/constants";

export function ActionButtons({ onEvaluate, canEvaluate, loading }) {
  const isBuilding = loading === LOADING_STATES.BUILDING;
  const isEvaluating = loading === LOADING_STATES.EVALUATING;

  const isEvaluateDisabled = !canEvaluate || isBuilding || isEvaluating;

  return (
    <Group justify="center" gap="md">
      <Button
        leftSection={<IconArrowRight size={18} />}
        onClick={onEvaluate}
        disabled={isEvaluateDisabled}
        loading={isEvaluating || isBuilding}
        color="orange"
        size="lg"
      >
        Run Evaluation
      </Button>
    </Group>
  );
}
