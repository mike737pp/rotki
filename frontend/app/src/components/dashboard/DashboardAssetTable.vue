<template>
  <v-card>
    <v-card-title>
      {{ title }}
      <v-spacer />
      <v-text-field
        v-model="search"
        outlined
        dense
        prepend-inner-icon="mdi-magnify"
        :label="$t('dashboard_asset_table.search')"
        class="pa-0 ma-0 dashboard-asset-table__search"
        single-line
        hide-details
      />
    </v-card-title>
    <v-card-text>
      <v-data-table
        class="dashboard-asset-table__balances"
        :headers="headers"
        :items="balances"
        :search="search"
        :loading="loading"
        sort-by="usdValue"
        sort-desc
        :footer-props="footerProps"
      >
        <template #header.usdValue>
          <div class="text-no-wrap">
            {{
              $t('dashboard_asset_table.headers.value', {
                symbol: currencySymbol
              })
            }}
          </div>
        </template>
        <template #header.price>
          <div class="text-no-wrap">
            {{
              $t('dashboard_asset_table.headers.price', {
                symbol: currencySymbol
              })
            }}
          </div>
        </template>
        <template #item.asset="{ item }">
          <asset-details :asset="item.asset" />
        </template>
        <template #item.amount="{ item }">
          <amount-display :value="item.amount" />
        </template>
        <template #item.usdValue="{ item }">
          <amount-display
            show-currency="symbol"
            :fiat-currency="item.asset"
            :amount="item.amount"
            :value="item.usdValue"
          />
        </template>
        <template #item.price="{ item }">
          <amount-display
            show-currency="symbol"
            fiat-currency="USD"
            tooltip
            :value="prices[item.asset] ? prices[item.asset] : '-'"
          />
        </template>
        <template #item.percentage="{ item }">
          <percentage-display :value="percentage(item.usdValue)" />
        </template>
        <template #no-results>
          <span class="grey--text text--darken-2">
            {{
              $t('dashboard_asset_table.no_search_result', {
                search
              })
            }}
          </span>
        </template>
        <template v-if="balances.length > 0 && search.length < 1" #body.append>
          <tr
            v-if="$vuetify.breakpoint.smAndUp"
            class="dashboard-asset-table__balances__total font-weight-medium"
          >
            <td colspan="3">{{ $t('dashboard_asset_table.total') }}</td>
            <td class="text-end">
              <amount-display
                :fiat-currency="currencySymbol"
                :value="
                  balances
                    | aggregateTotal(
                      currencySymbol,
                      exchangeRate(currencySymbol),
                      floatingPrecision
                    )
                "
                show-currency="symbol"
              />
            </td>
            <td />
          </tr>
          <tr v-else>
            <td>
              <v-row class="justify-space-between">
                <v-col cols="auto" class="font-weight-medium">
                  {{ $t('dashboard_asset_table.total') }}
                </v-col>
                <v-col cols="auto">
                  <amount-display
                    :fiat-currency="currencySymbol"
                    :value="
                      balances
                        | aggregateTotal(
                          currencySymbol,
                          exchangeRate(currencySymbol),
                          floatingPrecision
                        )
                    "
                    show-currency="symbol"
                  />
                </v-col>
              </v-row>
            </td>
          </tr>
        </template>
      </v-data-table>
    </v-card-text>
  </v-card>
</template>

<script lang="ts">
import { default as BigNumber } from 'bignumber.js';
import { Component, Prop, Vue } from 'vue-property-decorator';
import { DataTableHeader } from 'vuetify';
import { mapGetters, mapState } from 'vuex';
import { footerProps } from '@/config/datatable.common';
import { CURRENCY_USD } from '@/data/currencies';
import { AssetBalance, AssetPrices } from '@/store/balances/types';

@Component({
  computed: {
    ...mapGetters('session', ['floatingPrecision', 'currencySymbol']),
    ...mapGetters('balances', ['exchangeRate']),
    ...mapGetters('statistics', ['totalNetWorthUsd']),
    ...mapState('balances', ['prices'])
  }
})
export default class DashboardAssetTable extends Vue {
  @Prop({ required: false, type: Boolean, default: false })
  loading!: boolean;
  @Prop({ required: true, type: String })
  title!: string;
  @Prop({ required: true, type: Array })
  balances!: AssetBalance[];

  totalNetWorthUsd!: BigNumber;
  floatingPrecision!: number;
  currencySymbol!: string;
  prices!: AssetPrices;
  exchangeRate!: (currency: string) => number | undefined;

  search: string = '';

  readonly footerProps = footerProps;
  get headers(): DataTableHeader[] {
    return [
      {
        text: this.$tc('dashboard_asset_table.headers.asset'),
        value: 'asset',
        cellClass: 'asset-info'
      },
      {
        text: this.$t('dashboard_asset_table.headers.price', {
          symbol: this.currencySymbol ?? CURRENCY_USD
        }).toString(),
        value: 'price',
        align: 'end',
        sortable: false
      },
      {
        text: this.$tc('dashboard_asset_table.headers.amount'),
        value: 'amount',
        align: 'end',
        cellClass: 'asset-divider'
      },
      {
        text: this.$t('dashboard_asset_table.headers.value', {
          symbol: this.currencySymbol ?? CURRENCY_USD
        }).toString(),
        value: 'usdValue',
        align: 'end',
        class: 'text-no-wrap'
      },
      {
        text: this.$tc('dashboard_asset_table.headers.percentage'),
        value: 'percentage',
        align: 'end',
        cellClass: 'asset-percentage',
        class: 'text-no-wrap',
        sortable: false
      }
    ];
  }

  percentage(value: BigNumber): string {
    return value.div(this.totalNetWorthUsd).multipliedBy(100).toFixed(2);
  }
}
</script>

<style scoped lang="scss">
::v-deep {
  .asset-divider {
    width: 100%;

    @media (min-width: 2000px) {
      width: 50%;
    }
  }

  .asset-info {
    @media (min-width: 2000px) {
      width: 300px;
    }
  }

  .asset-percentage {
    width: 120px;

    @media (min-width: 2000px) {
      width: 200px;
    }
  }
}

.dashboard-asset-table {
  &__search {
    max-width: 450px;
  }

  &__balances {
    &__total {
      &:hover {
        background-color: transparent !important;
      }
    }
  }
}
</style>
