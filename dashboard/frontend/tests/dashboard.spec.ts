import { expect, Page, test } from '@playwright/test';

const mockSolutions = [
  {
    'Solution ID': 'sol-1',
    'Case Study': 'Cameo_datacenter',
    'Location Scenario': 'Alpha',
    'Battery Cost ($M)': 12.3,
    'Cable Material Cost ($M)': 8.7,
    'Day-Ahead Revenue ($k)': 30.0,
    weighted_score: 10.25,
    x_coord: 1,
    y_coord: 4,
    label: 'cost_optimized',
  },
  {
    'Solution ID': 'sol-2',
    'Case Study': 'Cameo_datacenter',
    'Location Scenario': 'Beta',
    'Battery Cost ($M)': 14.1,
    'Cable Material Cost ($M)': 7.2,
    'Day-Ahead Revenue ($k)': 25.0,
    weighted_score: 7.9,
    x_coord: 2,
    y_coord: 5,
    label: 'balanced',
  },
  {
    'Solution ID': 'sol-3',
    'Case Study': 'Cameo_datacenter',
    'Location Scenario': 'Gamma',
    'Battery Cost ($M)': 10.4,
    'Cable Material Cost ($M)': 9.8,
    'Day-Ahead Revenue ($k)': 34.0,
    weighted_score: 14.8,
    x_coord: 3,
    y_coord: 6,
    label: 'revenue_focused',
  },
];

async function mockDashboardApi(page: Page): Promise<void> {
  await page.route('**/api/case-studies', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ files: ['Cameo_datacenter', 'MoCoDo_v2'] }),
    });
  });

  await page.route('**/api/init?*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        filters: [
          {
            key: 'Location Scenario',
            name: 'Location Scenario',
            values: ['Alpha', 'Beta', 'Gamma'],
          },
          {
            key: 'Technology',
            name: 'Technology',
            values: ['A', 'B'],
          },
        ],
        objectives: {
          'Battery Cost ($M)': 40,
          'Cable Material Cost ($M)': 35,
          'Day-Ahead Revenue ($k)': 25,
        },
      }),
    });
  });

  await page.route('**/api/objective?*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        weights_used: {
          'Battery Cost ($M)': 40,
          'Cable Material Cost ($M)': 35,
          'Day-Ahead Revenue ($k)': 25,
        },
      }),
    });
  });

  await page.route('**/api/solutions?*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        solutions: mockSolutions,
        index_keys: ['Solution ID', 'Case Study', 'Location Scenario'],
        hyperparameter_keys: [],
        decision_keys: ['Battery Cost ($M)', 'Cable Material Cost ($M)'],
        objective_keys: ['Day-Ahead Revenue ($k)'],
        additional_cols: ['weighted_score', 'x_coord', 'y_coord', 'label'],
        ranks: {
          'Design-A,Alpha': {
            'Battery Cost ($M)': 12.3,
            'Cable Material Cost ($M)': 8.7,
            'Day-Ahead Revenue ($k)': 30,
          },
          'Design-B,Beta': {
            'Battery Cost ($M)': 14.1,
            'Cable Material Cost ($M)': 7.2,
            'Day-Ahead Revenue ($k)': 25,
          },
          'Design-C,Gamma': {
            'Battery Cost ($M)': 10.4,
            'Cable Material Cost ($M)': 9.8,
            'Day-Ahead Revenue ($k)': 34,
          },
        },
      }),
    });
  });

  await page.route('**/api/lmp?*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        data: [
          {
            INTERVALSTARTTIME_GMT: '1',
            time: 1,
            sim: 'sim-1',
            LMP: '31.25',
            'Case Study': 'Cameo_datacenter',
            Location: 'Alpha',
          },
          {
            INTERVALSTARTTIME_GMT: '2',
            time: 2,
            sim: 'sim-1',
            LMP: '35.75',
            'Case Study': 'Cameo_datacenter',
            Location: 'Alpha',
          },
        ],
      }),
    });
  });

  await page.route('**/api/specializers?*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        solutions: [mockSolutions[0], mockSolutions[2]],
        ranks: {
          'Design-A,Alpha': {
            'Battery Cost ($M)': 12.3,
            'Cable Material Cost ($M)': 8.7,
            'Day-Ahead Revenue ($k)': 30,
          },
          'Design-C,Gamma': {
            'Battery Cost ($M)': 10.4,
            'Cable Material Cost ($M)': 9.8,
            'Day-Ahead Revenue ($k)': 34,
          },
        },
      }),
    });
  });
}

async function waitForDashboard(page: Page): Promise<void> {
  await expect(page.getByText('Visual Reasoning for Decision Making')).toBeVisible();
  await expect(page.getByRole('tab', { name: 'Decision Making' })).toBeVisible();
  await expect(page.getByRole('tab', { name: 'Scenario Comparison' })).toBeVisible();
  await expect(page.getByText('Objective Weights')).toBeVisible();
}

test.describe('pyMOODS dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await mockDashboardApi(page);
    await page.goto('/');
    await waitForDashboard(page);
  });

  test('loads key dashboard sections', async ({ page }) => {
    await expect(page.locator('div[role="combobox"]').first()).toContainText('Cameo_datacenter');
    await expect(page.getByText('Use Case', { exact: true })).toBeVisible();
    await expect(page.getByText('Filters')).toBeVisible();
    await expect(page.getByText('Objective Functions')).toBeVisible();
    await expect(page.getByText('Decision Variables')).toBeVisible();
  });

  test('sorts summary table by weighted sum', async ({ page }) => {
    await expect(page.getByRole('cell', { name: 'sol-1' })).toBeVisible();

    const weightedSumHeader = page.getByRole('columnheader', { name: /Weighted Sum/i });
    await weightedSumHeader.click();
    await weightedSumHeader.click();

    const firstRowFirstCell = page.locator('tbody tr').first().locator('td').first();
    await expect(firstRowFirstCell).toHaveText('sol-3');
  });

  test('updates specializers slider and shows specialized state', async ({ page }) => {
    const slider = page.locator('input[type="range"]').first();
    await slider.click();
    await slider.press('ArrowRight');

    await expect(page.getByText(/Minimum Number of Specializers:\s*7/)).toBeVisible();
    await expect(page.getByText('Showing specialized solutions only')).toBeVisible();
  });
});
