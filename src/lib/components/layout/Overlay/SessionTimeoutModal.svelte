<script>
	import { getContext, createEventDispatcher } from 'svelte';
	import Modal from '$lib/components/common/Modal.svelte';

	export let show = false;
	export let countdown = 0;

	const i18n = getContext('i18n');
	const dispatch = createEventDispatcher();

	const login = () => {
		location.href = '/auth';
	};
</script>

<Modal bind:show size="sm" dismissible={false}>
	<div class="p-6 text-center">
		<h3 class="mb-5 text-lg font-normal text-gray-500 dark:text-gray-400">
			{$i18n.t('Session Timeout Warning')}
		</h3>
		<p class="mb-5 text-sm text-gray-500 dark:text-gray-400">
			{$i18n.t('Your session is about to expire in')}: {Math.floor(countdown / 60)}m {Math.floor(
				countdown % 60
			)}s.<br />
			{$i18n.t('Do you want to extend it?')}
		</p>
		<div class="flex justify-center gap-4">
			<button
				type="button"
				class="text-white bg-blue-600 hover:bg-blue-800 focus:ring-4 focus:outline-none focus:ring-blue-300 dark:focus:ring-blue-800 font-medium rounded-lg text-sm inline-flex items-center px-5 py-2.5 text-center"
				on:click={() => {
					dispatch('extend');
					show = false;
				}}
			>
				{$i18n.t('Extend Session')}
			</button>
			<button
				type="button"
				class="text-gray-500 bg-white hover:bg-gray-100 focus:ring-4 focus:outline-none focus:ring-gray-200 rounded-lg border border-gray-200 text-sm font-medium px-5 py-2.5 hover:text-gray-900 focus:z-10 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-500 dark:hover:text-white dark:hover:bg-gray-600 dark:focus:ring-gray-600"
				on:click={login}
			>
				{$i18n.t('Log In')}
			</button>
		</div>
	</div>
</Modal>
