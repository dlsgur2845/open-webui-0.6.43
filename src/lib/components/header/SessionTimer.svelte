<script lang="ts">
	import { onDestroy, onMount } from 'svelte';
	import { user } from '$lib/stores';
	import { fade } from 'svelte/transition';

	let countdown = '';
	let interval: any;
	let showTimer = false;

	const formatTime = (seconds: number) => {
		const h = Math.floor(seconds / 3600);
		const m = Math.floor((seconds % 3600) / 60);
		const s = seconds % 60;
		if (h > 0) return `로그아웃 ${h}시간 ${m}분 남음`;
		return `로그아웃 ${m}분 ${s}초 남음`;
	};

	const updateTimer = () => {
		if ($user?.expires_at) {
			// Calculate remaining time based on server timestamp if available, otherwise simplified
			// Assuming expires_at is unix timestamp in seconds
			const now = Math.floor(Date.now() / 1000);
			// Ideally we should account for clock skew calculated in +layout.svelte,
			// but for visual display a few seconds off is acceptable or we can duplicate logic.
			// Let's use simple local time diff for now, assuming synced clocks or roughly correct.
			const diff = $user.expires_at - now;

			if (diff > 0) {
				countdown = formatTime(diff);
				showTimer = true;

				// Optional: visual urgency
				if (diff < 300) {
					// Less than 5 mins
					// color logic can be handled in template
				}
			} else {
				countdown = '0m 0s';
				showTimer = false; // or show 'Expired'
			}
		} else {
			showTimer = false;
		}
	};

	onMount(() => {
		updateTimer();
		interval = setInterval(updateTimer, 1000);
	});

	onDestroy(() => {
		if (interval) clearInterval(interval);
	});
</script>

{#if showTimer}
	<div
		class="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-gray-50 dark:bg-gray-850 border border-gray-100 dark:border-gray-800 text-xs font-medium text-gray-600 dark:text-gray-300 transition-colors"
		in:fade
	>
		<div class="size-1.5 rounded-full bg-green-500 animate-pulse"></div>
		<span>{countdown}</span>
	</div>
{/if}
