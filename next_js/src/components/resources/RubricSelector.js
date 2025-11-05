"use client";

import { useEffect, useState, useCallback } from "react";
import { Select, Stack, Paper, Text, Loader, Button } from "@mantine/core";
import { IconRefresh } from "@tabler/icons-react";

export function RubricSelector({ selectedRubric, onSelect, onLoad, onGet }) {
  const [rubrics, setRubrics] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState(selectedRubric?.id || null);

  const loadRubrics = useCallback(async () => {
    if (!onLoad || typeof onLoad !== "function") {
      setRubrics([]);
      return;
    }

    try {
      setLoading(true);
      const data = await onLoad();
      if (Array.isArray(data)) {
        setRubrics(data);
      } else {
        console.warn("Expected array but got:", typeof data);
        setRubrics([]);
      }
    } catch (error) {
      console.error("Failed to load rubrics:", error);
      setRubrics([]);
    } finally {
      setLoading(false);
    }
  }, [onLoad]);

  useEffect(() => {
    loadRubrics();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (selectedRubric) {
      setSelectedId(selectedRubric.id);
    }
  }, [selectedRubric]);

  const handleSelect = async (value) => {
    if (!value || !onGet || typeof onGet !== "function") return;
    setSelectedId(value);
    try {
      const rubric = await onGet(value);
      if (onSelect && typeof onSelect === "function") {
        onSelect(rubric);
      }
    } catch (error) {
      console.error("Failed to get rubric:", error);
    }
  };

  const rubricOptions = rubrics.map((r) => ({
    value: r.id,
    label: `${r.course} - ${r.assignment} (${r.version})`,
  }));

  return (
    <Stack gap="sm">
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <Text size="sm" fw={600}>
          Pilih Rubric
        </Text>
        <Button
          variant="subtle"
          size="xs"
          onClick={loadRubrics}
          leftSection={<IconRefresh size={14} />}
        >
          Refresh
        </Button>
      </div>

      {loading ? (
        <Loader size="sm" />
      ) : (
        <Select
          placeholder="Pilih rubric..."
          value={selectedId}
          onChange={handleSelect}
          data={rubricOptions}
          searchable
          clearable
        />
      )}

      {selectedRubric && (
        <Paper p="xs" withBorder radius="sm" bg="orange.0">
          <Text size="xs" fw={600} c="orange.7">
            Selected: {selectedRubric.assignment}
          </Text>
          <Text size="xs" c="dimmed">
            {selectedRubric.items?.length || 0} items
          </Text>
        </Paper>
      )}
    </Stack>
  );
}
